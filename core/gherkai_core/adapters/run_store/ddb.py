"""DynamoDBRunStore（ADR 0030 决定六）：RunStore port 的 DynamoDB 实装。

对拍 `LocalRunStore` 的行为（同一批 round-trip/生命周期/报错语义），只换落点为 DDB。**云端 adapter，需 boto3**
（`gherkai-core[aws]` optional extra，缺它 import 本模块不崩、构造时才友好报错，守 [0016] 窄腰）。

表 schema（决定六）：单表、分区键字段 `run_id` + 排序键字段 `item_type`（取值 `'META'`/`'STATE'`）——
提交记录的头与 RunState **分两 item**（同 run_id、item_type 各异；同分区键下一次 Query 可一次捞回该 run 的两个 item）：
- **META item**（提交记录的头，ADR 0030 决定六「云端提交记录」条）：`{run_id, item_type='META', schema_version, cli_version,
  deadline_at, jobs_ref, meta_json=<运行定义去掉 jobs 之后的 json.dumps>}`（三个顶层属性是 meta_json 里同名键的副本，见 `create_run`）。
  运行定义的 jobs 整份在产物桶里的 jobs 对象（同包 `jobs_object.py`），`jobs_ref` 是它的 `s3://` 地址；头不随 job 数增长。提交记录
  **write-once（create_run）/ read-whole（load_run_meta）**，从不单元素更新，所以 meta_json 整体存 JSON 字符串。
- **STATE item**：`{run_id, item_type='STATE', status, status_group, started_at?, ended_at?, high_water_mark?, message?,
  claim_count, write_seq, jobs=<原生 Map>}`（`?` = omit-when-None；`message` 是 run 级说明，随结束写的两个入口 `end_run` 与
  `end_run_as_error` 写入；
  `high_water_mark` 与 `claim_count` 是本 item 的两个数值属性，读回 Decimal 转 int——前者只在无状态批量运行的投影写时有值，投影写的
  ConditionExpression 按它做数值守卫，见 ADR 0034 机制三；后者是认领计数，create_run 恒写、认领成功时原子加一、缺属性读作 0，
  见 ADR 0034 机制三「run 级状态只进不退」条①；`write_seq` 是写入序号，见 `_write_seq_increment`；`status_group` 是由
  run 级 `status` 派生的状态分组、状态分组索引的分区键，写入规则见 `status_group`），另有两个
  **可选顶层标记**：`detached`（kicker 的 Stream filter 认它）与 `worker_task_def_arns`（ADR 0038，
  清理 pass 的运行中 run 引用检查经状态分组索引读 `live` 分组里各 run 的这个属性）——两者都是「DDB 侧要查得动」才摊到顶层的。
  这类顶层附加属性只在 create_run 时写下；之后的写全是 update_item，不提及的属性原样保留。
  jobs **必须原生 Map** 才能 `SET jobs.#sid.<属性>` 按 scope_id 单元素刷；其 entry 全是 str（无 float），
  原生 Map 无 Decimal 顾虑。jobs 的写法有两种：认领、投影与 `update_job_state` 按 scope_id 逐属性写单个 job，条目里不认识的属性
  不提及；`commit_job_states`、`end_run` 与结束写的 error 变体 `end_run_as_error` 以写入序号为条件整体替换 jobs（ADR 0034 机制三②）：
  前两者的替换内容由按模型读到的运行态算出，读到的条目里不认识的属性并进去，error 变体只认运行态的公共部分、读到的条目原样复制
  （ADR 0030 决定四「改写运行态时原样保留不认识的部分」条）。

字段仍源于 `serialize`（单一真理源）：`run_meta_to_dict` 的产出拆成两份，jobs 进 jobs 对象、其余进 meta_json；STATE 的标量 + jobs 各 entry
的字段集取自 `run_state_to_dict`，只是 jobs 的**容器形状**在本 adapter 从 list 特化成 Map（非第二真理源）。

列举（`list_runs`，ADR 0041 决策七「云端实现」）经 runs 表的状态分组索引找 run_id（分区键 `status_group`、排序键 `run_id`，
只有 STATE item 带分组属性，ADR 0030 决定六），再用 `BatchGetItem` 强一致读回 STATE 与 META；索引名由组合根经构造参数注入
（命名真源在 runtime，core 不 import 它）。守 ADR 0038 的红线：runs 表随历史单调增长，本 adapter 不 Scan。

建表责任在 IaC/组合根、非本 adapter——adapter 假定表已存在（决定六；测试由 conftest fixture 建表）。
"""
from __future__ import annotations

import json
import time
from collections.abc import Sequence

from gherkai_core.adapters._boto import require_boto3
from gherkai_core.adapters.run_store.jobs_object import S3JobsObjects
from gherkai_core.errors import DefinitionContractError, RunAlreadyExists
from gherkai_core.model import TERMINAL_STATUSES, JobState, RunListing, RunMeta, RunState, Status
from gherkai_core.run_status import CommitOutcome, RunEnding, check_new_run, check_running_write, commit_applied, ending_applied
from gherkai_core.serialize import (
    JOB_STATE_KEYS,
    UNREADABLE_RECORD_ERRORS,
    definition_from_json,
    require_definition_schema,
    require_listing_header,
    require_listing_state,
    run_meta_from_dict,
    run_meta_to_dict,
)

# 排序键字段名（区分同一 run 的 definition/运行态 item，见决定六）——用 item_type 不用缩写 sk
_ITEM_TYPE_ATTR = "item_type"
_META = "META"    # item_type 取值：definition item
_STATE = "STATE"  # item_type 取值：运行态 item

# STATE item 顶层属性：本 run 用到的 worker task-def revision ARN 列表（ADR 0038「不变量」清理 pass 的
# 运行中 run 引用检查按它判断某 revision 是否仍被引用——definition 里也有同一批 ARN，但那在 meta_json
# 字符串内、DDB 查不动，故**同时**摊平成顶层属性，沿用 `detached` 顶层标记先例）。
# **写端在此、读端的命名真源在 `gherkai_runtime.names.STATE_WORKER_TASK_DEF_ARNS_ATTR`**：core 是窄腰下层、
# 不 import 组合根共享层，故字面量两处各有；漂移由 runtime 侧的对拍测试挡（那里能同时 import 两边）。
_WORKER_TASK_DEF_ARNS_ATTR = "worker_task_def_arns"

# STATE item 顶层属性：状态分组，runs 表状态分组索引的分区键（ADR 0030 决定六「runs 表只有一个 GSI」条）。META item 不带它，
# 索引的稀疏由此构造。写端在此、读端的命名真源在 `gherkai_runtime.names`（`STATE_STATUS_GROUP_ATTR`、`STATUS_GROUP_LIVE`），
# 字面量两处各有的理由与漂移护栏同上条。
_STATUS_GROUP_ATTR = "status_group"
_STATUS_GROUP_LIVE = "live"  # 非终态共用的分组值；不与任何 Status 值相同，终态分组取终态的状态值


def status_group(status: Status) -> str:
    """run 级状态 → 状态分组（ADR 0030 决定六）：非终态取 `live`，终态取该终态的状态值。

    写入规则：每一处写 run 级 `status` 的地方都由本函数从这次写入的 `status` 算出分组、写在同一次写里（put_item 经
    `_state_scalars`，update_item 经 `_run_status_assignment`）；不写 run 级 `status` 的写不碰分组属性，写之前缺它的记录写之后
    仍缺，这类写有投影的标量一步，以及投影里 pending 的那些 job 的逐 job 写。分组只服务这个索引；本机后端没有索引，不写它。
    """
    return status.value if status in TERMINAL_STATUSES else _STATUS_GROUP_LIVE


def _run_status_assignment(status: Status) -> tuple[str, dict, dict]:
    """update_item 里写 run 级 `status` 的 SET 片段，连同由它派生的状态分组（同一次写，写入规则见 `status_group`）。

    返回（片段, ExpressionAttributeNames, ExpressionAttributeValues），调用方并入各自的表达式；`#st` 与条件里的 `#st` 同指
    `status`，占位值名 `:rst` / `:rsg` 不与各调用方条件里的占位值重名。"""
    return ("#st = :rst, #sg = :rsg",
            {"#st": "status", "#sg": _STATUS_GROUP_ATTR},
            {":rst": status.value, ":rsg": status_group(status)})


# STATE item 顶层属性：写入序号（ADR 0030 决定六「STATE item 带写入序号」条、ADR 0034 机制三②）。只在 DDB 一侧有，不进 RunState：
# 本机的写在文件锁内读改写，不需要它。
_WRITE_SEQ_ATTR = "write_seq"


def _write_seq_increment() -> tuple[str, dict, dict]:
    """update_item 里把写入序号加一的 SET 片段（create_run 写初值 0；ADR 0030 决定六「STATE item 带写入序号」条）。

    改变了整体替换所写内容（jobs 与 run 状态）的写在同一次写里带上它：认领、终态写、结束写的两个入口，以及投影的逐 job 写（它只在这次
    写提及的字段与库中此刻的值至少一项不同时写成）。执行中的写 `update_job_state` 写成即带上、不比较内容。投影的标量一步只写 HWM，
    不带它：整体替换不写 HWM，那一步没有可被盖掉的内容。理由：整体替换 jobs 的写入口只以「序号等于读到的值」为条件，一次改变了这些
    内容而不加一的写若落在整体替换的读与写之间，就会被那次整体替换盖掉；不改变这些内容的写若也加一，只会把以序号为条件的写挤去重读
    （ADR 0034 机制三②与「逐 job 写：内容不变不写，注定不成立的不发」段）。缺属性按 0 起算（`if_not_exists`，同认领计数）。返回
    （片段, ExpressionAttributeNames, ExpressionAttributeValues），占位名 `#ws`、占位值 `:ws0` / `:ws1` 不与各调用方重名。"""
    return ("#ws = if_not_exists(#ws, :ws0) + :ws1", {"#ws": _WRITE_SEQ_ATTR}, {":ws0": 0, ":ws1": 1})


# 运行态公共部分里状态的取值（ADR 0037 决策 7「运行态的公共部分」：七个取值固定，pending 与 running 表示未结束）。结束写的 error
# 变体按它们读 STATE，不经 Status 与本格式的模型。
_STATUS_VALUES = frozenset(s.value for s in Status)
_OPEN_STATUS_VALUES = frozenset({Status.PENDING.value, Status.RUNNING.value})


def _is_integral_number(value) -> bool:
    """value 是不是整数值的数（DynamoDB 的数值读回为 Decimal；bool 不算）。"""
    from decimal import Decimal

    if isinstance(value, bool):
        return False
    if isinstance(value, int):
        return True
    return isinstance(value, Decimal) and value.is_finite() and value == value.to_integral_value()


# 整体替换 jobs 的三个写入口条件不成立时重读再算（ADR 0034 机制三②）：每次条件不成立都说明读与写之间有别的写落下。至多重试
# _REPLACE_MAX_RETRIES 次，第 k 次重试之前等 _REPLACE_BACKOFF_S * 2 ** (k - 1) 秒：并发的投影按 job 逐个写、每次改变了内容的写都让
# 序号加一，一个 job 多的 run 上它持续的时间可能长于一次读与写，退避让这次写在它写完之后再读。全部重试用尽约等十秒，仍不成立即抛
# `RunStateWriteContended`。
_REPLACE_MAX_RETRIES = 10
_REPLACE_BACKOFF_S = 0.01


class RunStateWriteContended(RuntimeError):
    """`commit_job_states`、`end_run` 或 `end_run_as_error` 重读再算的次数用尽，每一次都被读与写之间落下的别的写挡下：这次没有写成，
    运行态不因它改变。调用方按写不进运行态处理（与存储不可达同类）。`table` 是 runs 表名，`run_id` 是这个 run，`attempts` 是写的
    次数。"""

    def __init__(self, table: str, run_id: str, attempts: int) -> None:
        super().__init__(f"写入运行状态表 {table} 里 run {run_id} 的状态时，连续 {attempts} 次都有同时进行的其他写入先落下，"
                         "这次没有写成；请稍后重试。")
        self.table = table
        self.run_id = run_id
        self.attempts = attempts


class RunStateUnreadable(ValueError):
    """读到的 STATE 里，运行态的公共部分读不出（ADR 0037 决策 7「运行态的公共部分」）：结束写的 error 变体（`end_run_as_error`）读到的
    run 级状态、jobs 的形态、各条目的状态或写入序号不合约定的形态，或另两个整体替换 jobs 的写入口读到的写入序号不是整数（见
    `_seen_write_seq`）。这次没有写，运行态不变。

    error 变体的调用方按后端各入口共用的闸里「公共部分读不出」同样处理（ADR 0054 决策九「落实时，后端各入口先过同一道闸」第一步：只记
    日志、不写、不推进），不按写失败处理。它是 ValueError 的子类，落在 `serialize.UNREADABLE_RECORD_ERRORS` 的「读到了内容而解析不了」
    口径之内，按这一口径处理读不出的调用方（如处置）对它同样处理；单设一个类型，是为了让 error 变体的调用方与 STATE 不存在、run 已
    结束（返回 False）分得清。`table` 是 runs 表名，`run_id` 是这个 run。"""

    def __init__(self, table: str, run_id: str, what: str) -> None:
        super().__init__(f"读取运行状态表 {table} 里 run {run_id} 的状态记录时发现{what}，记录读不出，这次没有改写它。")
        self.table = table
        self.run_id = run_id


# 列举的读回（ADR 0041 决策七「云端实现」）：BatchGetItem 每次请求至多 100 个键（DynamoDB 服务限额）；返回的未处理键带退避
# 重试、次数有界，首次重试前等 _BATCH_GET_BACKOFF_S 秒、之后每次翻倍。
_BATCH_GET_MAX_KEYS = 100
_BATCH_GET_MAX_RETRIES = 5
_BATCH_GET_BACKOFF_S = 0.05
# 读回只取运行态、detached 标记与头部要用的属性：META 的 meta_json 带额外请求头与会话预热地址，清单用不到，不随清单传回；
# worker_task_def_arns 只服务清理的引用检查。投影只减少传回的数据，读量仍按整个 item 计。
_LISTING_ATTRS = ("run_id", _ITEM_TYPE_ATTR, "status", "started_at", "ended_at", "high_water_mark", "message", "claim_count",
                  "jobs", "detached", "schema_version", "cli_version")


class RunListingIncomplete(RuntimeError):
    """列举 run 时批量读回重试耗尽、仍有 run 没有读回（ADR 0041 决策七「云端实现」）：不给出缺行的清单，调用方按读不到这个后端
    处理（`list-runs` 以退出码 2 结束）。`table` 是 runs 表名，`missing` 是没有完整读回的 run 数：重试耗尽那一批里剩下的，加上
    因此不再发出的后续各批里的；此前各批已完整读回的不计。按页补读时（`limit` 给出）每页单独读回，只计出错的这一页，还没有查到的
    后续各页不在其内。"""

    def __init__(self, table: str, missing: int, retries: int) -> None:
        super().__init__(f"读取运行状态表 {table} 时重试 {retries} 次后仍有 {missing} 个 run 没有读回（通常是读取被限流），"
                         "为免给出缺行的清单，这次没有列出；请稍后重试。")
        self.table = table
        self.missing = missing


def _schema_version_attr(item: dict) -> int:
    """META item 顶层的 schema_version 属性 → 整数：缺这个属性读作 0（早于结构版本号的写端）；DDB 把数值还成 Decimal，须为整数值；
    显式 null（DDB 的 NULL 类型，读回为 None）、bool、字符串、带小数的值都是定义违约——与本机读头（serialize.definition_schema_version）
    同一口径：区分「缺键」与「值为 null」，不静默转换。"""
    from decimal import Decimal

    from gherkai_core.errors import DefinitionContractError

    if "schema_version" not in item:
        return 0
    v = item["schema_version"]
    if isinstance(v, bool):
        raise DefinitionContractError(f"META 的 schema_version 须为整数，现为 {v!r}")
    if isinstance(v, int):
        return v
    if isinstance(v, Decimal) and v == v.to_integral_value():
        return int(v)
    raise DefinitionContractError(f"META 的 schema_version 须为整数，现为 {v!r}")


# jobs Map 条目里属于 JobState 模型的属性（已知键集）：模型的键集登记在 `serialize.JOB_STATE_KEYS`，云端条目以 scope_id 为 Map 的键、
# 条目里没有 scope_id 这一项。整体替换 jobs 的两个按模型的写入口据它分出读到的条目里不认识的属性并进要写下的条目，执行中的写据它
# 逐属性写模型里的键（ADR 0030 决定四「改写运行态时原样保留不认识的部分」条）。
_JOB_ITEM_KEYS = JOB_STATE_KEYS - {"scope_id"}


def _job_state_to_item(js: JobState) -> dict:
    """JobState → DDB Map entry（字段集同 serialize；session_id、claimed_at、点名的标识 result_id 与 job 级说明 message 用
    omit-when-None，读回 .get 得 None，ADR 0030 决定五、决定六）。键都在 `_JOB_ITEM_KEYS` 之内。

    按模型写 jobs 的各处都经这里（结束写的 error 变体原样复制读到的条目、只改未结束条目的 status 与 message，不经这里）：建 run 的
    初始条目与执行中的写写下的模型键没有标识（只由终态写写下）；终态写与按模型算出的结束写整体替换 jobs 时（`_replace_state`），
    已点名的 job 的标识随条目一并写回，结束写因此不抹去此前各 job 的点名。"""
    d: dict = {"status": js.status.value}
    if js.session_id is not None:
        d["session_id"] = js.session_id
    if js.claimed_at is not None:
        d["claimed_at"] = js.claimed_at
    if js.result_id is not None:
        d["result_id"] = js.result_id
    if js.message is not None:
        d["message"] = js.message
    return d


def _unknown_job_attrs(entry: dict | None) -> dict:
    """读到的一个 jobs Map 条目里不在已知键集内的属性（别的写方写下、本版本不认识的）；条目不在时为空。"""
    return {k: v for k, v in (entry or {}).items() if k not in _JOB_ITEM_KEYS}


def _job_state_from_item(scope_id: str, m: dict) -> JobState:
    return JobState(scope_id=scope_id, status=Status(m["status"]),
                    session_id=m.get("session_id"), claimed_at=m.get("claimed_at"), result_id=m.get("result_id"),
                    message=m.get("message"))


def _state_scalars(state: RunState) -> dict:
    """RunState 顶层标量 → DDB 属性（status + omit-when-None 的起止、hwm 与 message + 恒写的认领计数，对齐
    serialize.run_state_to_dict），另加由 status
    派生的状态分组（不在 serialize 里：它只服务 DDB 的索引，写入规则见 `status_group`）。"""
    d: dict = {"status": state.status.value, _STATUS_GROUP_ATTR: status_group(state.status)}
    if state.started_at is not None:
        d["started_at"] = state.started_at
    if state.ended_at is not None:
        d["ended_at"] = state.ended_at
    if state.high_water_mark is not None:
        d["high_water_mark"] = state.high_water_mark  # ADR 0034 机制三（数值属性；无状态批量运行投影写时有）
    if state.message is not None:
        d["message"] = state.message  # run 级消息（ADR 0037 决策 7）
    d["claim_count"] = state.claim_count  # 认领计数（ADR 0034 机制三「run 级状态只进不退」条①）：恒写，数值属性
    return d


def _run_state_from_item(item: dict) -> RunState:
    """STATE item → RunState（jobs 原生 Map → dict[scope_id, JobState]）。`load_run_state` 与列举共用这一处，解析点只有一个。"""
    jobs = {
        sid: _job_state_from_item(sid, m)
        for sid, m in (item.get("jobs") or {}).items()
    }
    hwm = item.get("high_water_mark")
    return RunState(
        run_id=item["run_id"],
        status=Status(item["status"]),
        jobs=jobs,
        started_at=item.get("started_at"),
        ended_at=item.get("ended_at"),
        # DDB Number → int（boto3 resource 层给 Decimal）；缺键 → None（还没有过投影写）
        high_water_mark=int(hwm) if hwm is not None else None,
        message=item.get("message"),
        claim_count=int(item.get("claim_count", 0)),  # Decimal → int；缺属性读作 0（同 serialize 的读端）
    )


def _item_at_failed_condition(error) -> dict | None:
    """条件不成立的 update_item（带 `ReturnValuesOnConditionCheckFailure="ALL_OLD"`）带回的条目：条件判断那一刻的整个 item，转成与
    resource 层读回相同的形态；条目不存在时为 None。boto3 的 resource 层只转换成功的响应，出错响应里的条目仍是带类型标注的原始形态。"""
    raw = error.response.get("Item")
    if raw is None:
        return None
    from boto3.dynamodb.types import TypeDeserializer
    return TypeDeserializer().deserialize({"M": raw})


def _header_from_item(item: dict) -> tuple[int, str | None]:
    """META item 顶层的（结构版本, 写端 CLI 版本）：`peek_definition_header` 与列举共用。"""
    return _schema_version_attr(item), item.get("cli_version")


def _listed_from_live(row: RunListing, live: Sequence[Status]) -> bool:
    """经 `live` 分组找到的行是否列出（ADR 0041 决策七「云端实现」）：非终态的 run 属于哪个所请求的状态只由读回的状态判定，
    读回为未被请求的非终态的不列出；读回已到终态的与无法读取的照常列出、不复筛。"""
    return row.state is None or row.state.status in TERMINAL_STATUSES or row.state.status in live


class DynamoDBRunStore:
    """RunStore 的 DynamoDB 实装（组合根注入 boto3 表资源 + 表名）。行为对拍 LocalRunStore。"""

    def __init__(self, table, *, jobs_objects: S3JobsObjects | None = None, detached: bool = False,
                 list_index_name: str | None = None) -> None:
        """table：boto3 dynamodb.Table 资源（组合根注入；建表责任在 IaC，adapter 假定已存在）。

        jobs_objects：提交记录里 jobs 对象的存取（ADR 0030 决定六「云端提交记录」条的「装配」一项）。要建 run 或读整份运行定义的组合根
        注入它；只读头的（不带 `--wait` 的 `status`、`list-runs` 等）可以不注入。None（默认）时 `create_run` 与 `load_run_meta` 在任何
        读写之前抛错（装配缺失），对所有 run 都抛、与 run 的内容无关；其余方法照常。没有把 jobs 内联进头的形态。

        detached：本组合根是否「无状态批量运行的 submit」——True 则 create_run 的 STATE item 带
        `detached=true` 顶层标记，kicker Lambda 的 Stream filter 只认它（同步 `run --backend cloud` 的
        create_run 无此标记、不触发 kicker——否则双开推进器、重复起 task）。执行环境属性、不进 core 模型。

        list_index_name：列举用的状态分组索引名（ADR 0041 决策七；命名真源在 runtime，组合根注入）。只有 `list_runs` 用它；
        None（默认）时其余方法照常，调用 `list_runs` 即抛错（装配缺失）。就绪与否由组合根在装配时核，本 adapter 不查。
        """
        require_boto3("DynamoDBRunStore")
        self._table = table
        self._jobs_objects = jobs_objects
        self._detached = detached
        self._list_index_name = list_index_name

    def _require_jobs_objects(self) -> S3JobsObjects:
        """建 run 与读整份运行定义要用的 jobs 对象存取；没有注入即抛（装配缺失，与 `list_runs` 缺索引名同一种处理）。"""
        if self._jobs_objects is None:
            raise RuntimeError("本进程的 RunStore 没有配置提交记录里 job 列表的存取，建不了 run、也读不了整份提交记录"
                               "（配置缺失：起 RunStore 的地方须注入 jobs_objects）")
        return self._jobs_objects

    # ---- 生命周期写入口（ADR 0030 决定六）----

    def create_run(self, meta: RunMeta, initial_state: RunState) -> None:
        """run 开始：依次写 jobs 对象（运行定义的 jobs，产物桶里）、META（提交记录的头）、STATE（初始运行态，jobs 原生 Map），
        三次都是条件写，只在 run 不存在时整体成立（ADR 0030 决定六「建 run 是条件写」条，ADR 0054 决策五）。

        **次序是契约**：jobs 对象先于头，读者照头里的地址去取时它已在；头先于 STATE，kicker 由 STATE 的 INSERT 触发（detached 标记
        在 STATE 上，ADR 0034），触发时头必已在。

        **是否已存在只由这几次条件写裁定**，建 run 之前不先读：jobs 对象「键不存在才写」，META 与 STATE「条目不存在」，被挡下的都抛
        `RunAlreadyExists`，不改任何已有的记录。不覆盖已有的 jobs 对象由它的条件写保证、不靠随机段不相撞：没有这个条件时，两次建 run
        恰好得到同一个键，后到的一方会在它的头被拒之前就换掉先到一方的 jobs，写之前先读一次也挡不住读与写之间的另一方。各步失败时留下的
        原样留下、不补偿：jobs 对象的写失败或被挡下，什么都没写下；头的
        写失败或被挡下，留下一个没有记录指向的 jobs 对象；STATE 的写失败，头与 jobs 对象留在原处，这个 run 没有运行态、不被推进。
        别的错误原样抛出，调用方按写记录失败报出。

        没有注入 jobs 对象的存取即抛（装配缺失），先于没有 job 的运行定义的检查与任何读写。"""
        jobs_objects = self._require_jobs_objects()
        check_new_run(meta)  # 没有 job 的运行定义不建（先于任何写）
        run_id = meta.run_id
        meta_dict = run_meta_to_dict(meta)
        jobs_ref = jobs_objects.put(run_id, meta_dict.pop("jobs"))
        ccf = self._table.meta.client.exceptions.ConditionalCheckFailedException
        try:
            self._table.put_item(Item={
                "run_id": run_id,
                _ITEM_TYPE_ATTR: _META,
                # 结构版本、写端版本与运行期限是 meta_json 里同名键的副本（ADR 0037 决策 7、ADR 0054 决策二），值恒同（同一份
                # meta_dict）：只读头的各处用投影只取它们、不解析 meta_json、不取 jobs 对象
                "schema_version": meta_dict["schema_version"],
                "cli_version": meta_dict["cli_version"],
                "deadline_at": meta_dict["deadline_at"],
                "jobs_ref": jobs_ref,
                "meta_json": json.dumps(meta_dict, ensure_ascii=False),
            }, ConditionExpression="attribute_not_exists(run_id)")
            self._table.put_item(Item=self._state_item(meta, initial_state),
                                 ConditionExpression="attribute_not_exists(run_id)")
        except ccf as e:
            raise RunAlreadyExists(run_id) from e

    def _state_item(self, meta: RunMeta, initial_state: RunState) -> dict:
        """create_run 的 STATE item：初始运行态原样写入，另带只在建 run 时写下的顶层标记与写入序号的初值 0。"""
        return {
            "run_id": meta.run_id,
            _ITEM_TYPE_ATTR: _STATE,
            **({"detached": True} if self._detached else {}),  # kicker filter 只认带此标记的 INSERT
            # worker revision ARN 摊平进 STATE（ADR 0038）：omit-when-None/空 —— 本机后端与旧 definition
            # 无此值时不落属性（清理 pass 的 `contains` 过滤对缺属性的 item 天然不匹配，语义即「未引用」）。
            # 值取 definition 的 worker_task_defs，**去重后排序**成 list：属性只服务「有没有引用某 ARN」的
            # 存在性判定，稳定顺序让 item 可比对（两引擎共用同一 revision 时不留重复项）。
            **({_WORKER_TASK_DEF_ARNS_ATTR: sorted(set(meta.worker_task_defs.values()))}
               if meta.worker_task_defs else {}),
            **_state_scalars(initial_state),
            _WRITE_SEQ_ATTR: 0,  # 之后改变了 jobs 或 run 状态的 update_item 加一（见 `_write_seq_increment`）
            "jobs": {sid: _job_state_to_item(js) for sid, js in initial_state.jobs.items()},
        }

    def update_job_state(self, run_id: str, job_state: JobState) -> bool:
        """执行中的写（语义见 RunStore port）：按 scope_id 逐属性写 STATE.jobs 里一个条目的模型键，只发**一次** update_item。写入的
        不是 running、带点名的标识或带 job 级说明，即抛 ValueError（`run_status.check_running_write`），不发写。

        **逐属性写模型里的键**（ADR 0030 决定四「改写运行态时原样保留不认识的部分」条）：已知键集（`_JOB_ITEM_KEYS`）里这次有值的键
        SET，这次没有值的键 REMOVE，与本机整项替换模型键的结果相同；条目里不认识的属性不提及、原样保留。不整个替换条目：那样会抹掉
        别的写方写下、本版本不认识的属性。

        #sid 用 ExpressionAttributeNames 承载任意 scope_id（含 / : 中文，绕开保留字/特殊字符）；条目里的各属性名同样经占位名。

        **条件与写在同一次 update_item 里，不先读后写**（ADR 0034 机制三「run 级状态只进不退」条③）：STATE 存在、run 级为 pending
        或 running（run 到终态之后不再接受写，ADR 0054 决策五）、这个 job 在 Map 里且为 pending 或 running（不臆造 job；终态只写
        一次，ADR 0031 决定一·补）。写成时同一次写把 run
        级写成 running（连同状态分组，见 `status_group`）：写下的 job 是 running、run 未结束，按取法 run 即为 running（ADR 0031
        决定三）。
        条件不成立时这次写带回条件判断那一刻的 STATE（`ReturnValuesOnConditionCheckFailure`），据它分辨原因，不另读：
        - 没有带回条目：STATE 不存在，抛 FileNotFoundError。
        - run 级已是终态：返回 False。
        - 否则（这个 job 已是终态，或不在 Map 里）：不写，返回 True。
        返回值因而是条件判断那一刻 run 是否仍未结束，由条件写本身给出。写成时写入序号加一（见 `_write_seq_increment`）。
        """
        check_running_write(job_state)
        ccf = self._table.meta.client.exceptions.ConditionalCheckFailedException
        run_set, run_names, run_values = _run_status_assignment(Status.RUNNING)
        seq_set, seq_names, seq_values = _write_seq_increment()
        written = _job_state_to_item(job_state)
        # status 是 DDB 保留字；jobs.#sid.#st 与 run 级同名，共用占位名。其余模型键各用一个占位名，不必逐个核对哪些是保留字
        sets, removes = ["jobs.#sid.#st = :running"], []
        names = {"#sid": job_state.scope_id, **run_names, **seq_names}
        values = {":pending": Status.PENDING.value, ":running": Status.RUNNING.value, **run_values, **seq_values}
        for key in sorted(_JOB_ITEM_KEYS - {"status"}):
            names[f"#j_{key}"] = key
            if key in written:
                sets.append(f"jobs.#sid.#j_{key} = :j_{key}")
                values[f":j_{key}"] = written[key]
            else:
                removes.append(f"jobs.#sid.#j_{key}")  # 这次没有值的模型键删去；属性本来不在时这一项不改任何东西
        update = "SET " + ", ".join([*sets, run_set, seq_set]) + (" REMOVE " + ", ".join(removes) if removes else "")
        try:
            self._table.update_item(
                Key={"run_id": run_id, _ITEM_TYPE_ATTR: _STATE},
                UpdateExpression=update,
                ExpressionAttributeNames=names,
                ExpressionAttributeValues=values,
                ConditionExpression=("attribute_exists(run_id) AND #st IN (:pending, :running) "
                                     "AND jobs.#sid.#st IN (:pending, :running)"),
                ReturnValuesOnConditionCheckFailure="ALL_OLD",
            )
            return True
        except ccf as e:
            seen_item = _item_at_failed_condition(e)
        if seen_item is None:
            raise FileNotFoundError(f"update_job_state：STATE 不存在（须先 create_run）：{run_id}")
        return _run_state_from_item(seen_item).status not in TERMINAL_STATUSES

    def preflight(self) -> None:
        """探活（ADR 0030 决定七）：begin 前探表可达，表不存在/无权限即抛（cli 接住→以退出码 2 结束）。

        用 `table.load()`（即 DescribeTable）——轻量、只读、不写数据；表不存在抛 ResourceNotFoundException、
        无权限抛 AccessDenied，都原样冒泡由组合根 gated except 归到退出码 2。
        """
        self._table.load()

    # ---- 条件写（ADR 0034 机制三/四、ADR 0054 决策五）----
    # DDB 原生 ConditionExpression 做原子 CAS——对位 local 的 fcntl 文件锁（DDB 单 item 写天然原子、
    # 无需外部锁）。真 DDB 条件写行为由 ADR 0034 地基实测坐实（真 DDB 上 stale HWM 写被 CCF 挡、同 hwm 重复写
    # 幂等）；仓库内单测是 moto、与 local 逐条对拍（core/tests/test_conditional_writes.py）。
    # CCF=ConditionalCheckFailedException。

    def try_claim_job(self, run_id: str, scope_id: str, *, claimed_at: str | None = None) -> bool:
        """CAS：仅当 jobs[scope_id].status == 'pending' 且 run 未收尾才置 'running'（机制四）。CCF → False。

        同一条条件写把 run 级置 'running'（ADR 0034 机制三「run 级状态只进不退」条①）：顶层 `#st` 与 `jobs.#sid.#st`
        路径不重叠、可在同一更新表达式里写。条件不成立的三种原因（已被认领、job 不在 Map 里、run 已收尾）不区分，
        都不该由这次认领起 task；run 已收尾后不再接受新认领，此前已成功的认领不由此撤销。HWM 不变。
        随写 claimed_at（timeout 起算点，ADR 0034「job timeout」节）——与 status 同一条原子条件写。run 级连同状态分组一起写
        （见 `status_group`）：条件保证写之前 run 级非终态，库中分组本来就是 live，这次是同值写。
        认领计数在同一条写里加一（ADR 0034 机制三「run 级状态只进不退」条①）：缺属性按 0 起算（`if_not_exists`，与读端缺键读作 0、local 的读改写对拍）。
        写入序号同样在这条写里加一（见 `_write_seq_increment`）。
        """
        run_set, run_names, run_values = _run_status_assignment(Status.RUNNING)
        seq_set, seq_names, seq_values = _write_seq_increment()
        update = "SET jobs.#sid.#st = :running, " + run_set + ", #cc = if_not_exists(#cc, :zero) + :one, " + seq_set
        values = {":running": Status.RUNNING.value, ":pending": Status.PENDING.value, ":zero": 0, ":one": 1, **run_values,
                  **seq_values}
        if claimed_at is not None:
            update += ", jobs.#sid.claimed_at = :ca"
            values[":ca"] = claimed_at
        try:
            self._table.update_item(
                Key={"run_id": run_id, _ITEM_TYPE_ATTR: _STATE},
                UpdateExpression=update,
                ExpressionAttributeNames={"#sid": scope_id, "#cc": "claim_count", **run_names, **seq_names},
                ExpressionAttributeValues=values,
                # 仅当该 job 当前是 pending、run 级未收尾才认领
                ConditionExpression="jobs.#sid.#st = :pending AND #st IN (:pending, :running)",
            )
            return True
        except self._table.meta.client.exceptions.ConditionalCheckFailedException:
            return False

    def project_state(self, run_id: str, state: RunState) -> bool:
        """投影写（语义见 RunStore port）：put_item 表达不了逐 job 的条件，拆成两步，先标量、后逐 job，每一步各自带条件。

        **标量一步只推进 HWM、不写 run 状态、不加写入序号**：条件是库中 HWM 不大于这次投影的 HWM（缺属性同样成立）且 run 未结束
        （机制三①）；条件不成立（stale，或 run 已结束）即返回 False，不发逐 job 写。HWM 不在整体替换所写的内容里，这一步不把写入序号
        加一（见 `_write_seq_increment`）。

        **逐 job 写**（ADR 0034 机制三「② 的 job 级半边落地形态」段）：对每个 job（无效果的 pending 项除外，见末段）**逐属性**
        `SET jobs.#sid.status/.session_id/.claimed_at`，写下的 job 态不越过 running：投影里已有结果的 job 按 running 写，它的终态只由
        终态写记下。每一次逐 job 写的条件有四项：库中 HWM 不大于这次投影的 HWM（与标量一步同一道闸）；库中这个 job 不比投影更推进
        （写 running 时库中为 pending 或 running，写 pending 时库中为 pending）；这次写提及的字段（状态，以及投影带了时的会话、认领
        时刻）至少一项与库中此刻的值不同；run 未结束。被挡下的 job 静默跳过，不区分是哪一项挡下的：库中这个 job 已更推进（库中已是终态
        的 job 不被改写，终态只写一次，ADR 0031 决定一·补）、HWM 已被更高的投影越过、run 已结束（终态写或结束写落在两步之间，ADR 0054
        决策五），这次写都不该落下；内容与库中相同，这次写不必落下；job 不在 Map 里同样被条件挡下，不臆造 job。逐 job 写也带 HWM 的
        条件，因为标量一步之后、逐 job 的各次写之间，HWM 更高的投影可能完成标量写并写下同一个 job 的新值（如执行中 job 的另一个代表
        会话），只看等级与 run 未结束会把旧值写回。

        **内容与库中相同不写**（ADR 0034 机制三「逐 job 写：内容不变不写，注定不成立的不发」段）：比较的是写那一刻库中的值，不是调用方
        读到的 baseline，所以读与写之间别的写方写下同等级而字段不同的值时，这次写照样落下、以本次投影为准。可能缺失的会话与认领时刻
        写成显式的 `attribute_not_exists(...) OR ... <> ...`，不依赖缺失属性的比较怎样求值。逐 job 写只在写成时把写入序号加一：内容不变
        的写若照样加一，以序号为条件的终态写与结束写会被它挤去重读，而它并没有可被整体替换盖掉的内容。
        逐属性而非整个条目：update_item 不碰未提及的属性，投影没带的 session_id 与 claimed_at（claimed_at 只由 try_claim_job 写下、
        事件推演不出）保留库中值，对拍 local 的「投影缺字段回填库中值」，正确性不依赖调用方总传 baseline。两步非原子，但每步各自带
        条件，先标量、后 jobs 的次序保证中间态只会是「标量新、job 旧」，等价于一次携带旧 job 视图的合法投影，下一轮投影即收敛。传入的
        run 级 status、started_at、ended_at、message 都不写，库中值保留（started_at 由 create_run 写下）。

        **run 状态随把 job 写成 running 的那次逐 job 写**（ADR 0034 机制三「投影写的 run 状态按 0031 决定三的取法给出」段）：这次写同时
        把 run 状态连同状态分组写成 running（见 `status_group`），条件保证写之前 run 未结束，库中的 run 状态是 pending 或 running。job
        被投影写成 running 与 run 状态成为 running 出自同一次写，没有 run 级领先于 job 级的中间态。标量一步、投影里 pending 的那些 job
        的写与被挡下的写都不写 run 状态：没有 job 被写成 running 时库中的 run 状态原样保留（与 local 对拍），认领写下的 running 也不被
        拿着旧 baseline 的全 pending 投影改回 pending。

        **无效果的 pending 项不发写**（ADR 0034 机制三「逐 job 写：内容不变不写，注定不成立的不发」段「投影里 pending、没有会话与
        认领时刻的 job 不发写」条）：投影里 status 为 pending、session_id 与 claimed_at 都为空的 job 跳过。这类写只提及状态，条件既
        要求库中该 job 为 pending（不比投影更推进），又要求状态与库中不同，两者不能同时成立，写注定被挡下；该 job 不在 Map 里时同样
        被挡下。所以跳过与发出结果相同，依据只在写表达式本身，与调用方是否传 baseline 无关；而每次写都按整个 STATE item 的大小计费。
        三个条件缺一不可：投影一旦带了会话或认领时刻，这次写就可能改变库中值，照常发出。local 不需要同样跳过（锁内整份写回一次，
        写入次数不随 job 数增长）。"""
        new_hwm = state.high_water_mark or 0
        seq_set, seq_names, seq_values = _write_seq_increment()
        bounds = {":pending": Status.PENDING.value, ":running": Status.RUNNING.value}
        # 标量一步与每一次逐 job 写共用的两项条件：库中 HWM 不大于这次投影的 HWM（缺属性同样成立），且 run 未结束
        hwm_ok = "(attribute_not_exists(high_water_mark) OR high_water_mark <= :h)"
        run_open = "#st IN (:pending, :running)"
        ccf = self._table.meta.client.exceptions.ConditionalCheckFailedException
        try:
            self._table.update_item(
                Key={"run_id": run_id, _ITEM_TYPE_ATTR: _STATE},
                UpdateExpression="SET high_water_mark = :h",  # 只推进 HWM：不写 run 状态与分组，不加写入序号
                ConditionExpression=f"{hwm_ok} AND {run_open}",  # 条件不成立：stale，或 run 已结束
                ExpressionAttributeNames={"#st": "status"},
                ExpressionAttributeValues={":h": new_hwm, **bounds},
            )
        except ccf:
            return False
        # 逐 job 单调条件写（ADR 0034 机制三②与「② 的 job 级半边落地形态」段）：生命周期序 pending < running < 终态，写下的 job 态不越过
        # running，仅当库中这个 job 不比投影更推进才写（同为 running 时取本次投影的值；库中已是终态的不改）。嵌套路径与顶层的 run 状态
        # 共用占位名 #st，写法与 try_claim_job 相同
        run_set, run_names, run_values = _run_status_assignment(Status.RUNNING)
        for sid, js in state.jobs.items():
            target = Status.RUNNING if js.status in TERMINAL_STATUSES else js.status  # 投影不越过 running
            if target == Status.PENDING and js.session_id is None and js.claimed_at is None:
                continue  # 无效果的 pending 项不发写（等价性论证见 docstring 末段）
            sets = ["jobs.#sid.#st = :st", seq_set]
            names = {"#sid": sid, "#st": "status", **seq_names}
            values = {":st": target.value, ":h": new_hwm, **bounds, **seq_values}
            if target == Status.RUNNING:
                # 库中这个 job 须为 pending 或 running；run 状态与分组随这次写写成 running。job 不在 Map 里时条件同样不成立（不臆造
                # job，与 local 同样静默跳过；逐属性 SET 的父路径不存在会 ValidationException，条件先把它挡成 CCF）
                job_cond = "jobs.#sid.#st IN (:pending, :running)"
                sets.append(run_set)
                names.update(run_names)
                values.update(run_values)
            else:
                job_cond = "jobs.#sid.#st = :pending"
            # 这次写提及的字段至少一项与库中此刻的值不同（可能缺失的属性写成显式的不存在或不等，见 docstring）
            differs = ["jobs.#sid.#st <> :st"]
            if js.session_id is not None:  # 为 None 即不提及，库中值保留（回填兜底）
                sets.append("jobs.#sid.session_id = :sess")
                values[":sess"] = js.session_id
                differs.append("attribute_not_exists(jobs.#sid.session_id) OR jobs.#sid.session_id <> :sess")
            if js.claimed_at is not None:
                sets.append("jobs.#sid.claimed_at = :cat")
                values[":cat"] = js.claimed_at
                differs.append("attribute_not_exists(jobs.#sid.claimed_at) OR jobs.#sid.claimed_at <> :cat")
            try:
                self._table.update_item(
                    Key={"run_id": run_id, _ITEM_TYPE_ATTR: _STATE},
                    UpdateExpression="SET " + ", ".join(sets),
                    # 四项条件一律带上（ADR 0034 机制三「② 的 job 级半边落地形态」段）
                    ConditionExpression=f"{hwm_ok} AND {job_cond} AND ({' OR '.join(differs)}) AND {run_open}",
                    ExpressionAttributeNames=names,
                    ExpressionAttributeValues=values,
                )
            except ccf:
                # 库中这个 job 已结束或更推进、HWM 已被更高的投影越过、内容与库中相同，或 run 已结束：保留库中值，不回退
                continue
        return True

    # ---- run 的状态只由 job 的终态算出（ADR 0031 决定三）：两个写入口的作用由 run_status 给出，这里只负责读、写的条件与重试 ----
    # 两者的步骤相同：强一致读 STATE，按 run_status 的纯函数从读到的运行态算出要写下的运行态，再以「写入序号等于读到的值、run 未结束」
    # 为条件整体替换 jobs 并写下 run 状态（连同状态分组）；条件不成立即重读再算（ADR 0034 机制三②），次数上限见 `_REPLACE_MAX_RETRIES`。

    def commit_job_states(self, run_id: str, job_states: Sequence[JobState], *, ended_at: str) -> CommitOutcome:
        """带结果的 job 终态写（语义见 RunStore port）：每一轮按读到的运行态经 `run_status.commit_applied` 算出这次写的作用与结果。

        run 已结束（ALREADY_ENDED）时不写；给出的 job 在库中都已是终态时运行态不变，同样不写、返回 OPEN。否则发一次条件写（见
        `_replace_state`），写成即返回这一轮算出的结果，被挡下即重读再算：重读到 run 已结束返回 ALREADY_ENDED。每一轮都按这一轮读到的
        条目合并给出的 job（规则见 `run_status.commit_applied`）：读与写之间别的写为它写下的认领时刻在重读之后留下，写下的会话只在给出的
        job 没有会话时留下，两者都不被空值覆盖；每一轮用的都是同一组给出的 job，点名的标识因此不随重读改变。读不到 STATE 抛
        FileNotFoundError；参数不合要求时 commit_applied 在任何写之前抛 ValueError；要写时读到的写入序号不是整数抛
        `RunStateUnreadable`、不写。重试用尽抛 `RunStateWriteContended`。"""
        job_states = tuple(job_states)
        for attempt in range(_REPLACE_MAX_RETRIES + 1):
            self._back_off(attempt)
            item = self._read_state_item(run_id)
            if item is None:
                raise FileNotFoundError(f"commit_job_states：STATE 不存在（须先 create_run）：{run_id}")
            before = _run_state_from_item(item)
            after, outcome = commit_applied(before, job_states, ended_at=ended_at)
            if after is None or after == before:
                return outcome
            if self._replace_state(run_id, item, before, after):
                return outcome
        raise RunStateWriteContended(self._table.name, run_id, _REPLACE_MAX_RETRIES + 1)

    def end_run(self, run_id: str, ending: RunEnding, *, ended_at: str) -> bool:
        """结束写（语义见 RunStore port）：每一轮按读到的运行态经 `run_status.ending_applied` 算出要写下的运行态。

        STATE 不存在、run 已结束、或结束写不成立（不结束执行中 job 的来路，即 `ending.ends_running_jobs` 为 False，遇到 running 的
        job）时返回 False、不写。否则发一次条件写（见 `_replace_state`），写成返回 True，被挡下即重读再算：重读到 run 已结束返回 False；
        不结束执行中 job 的来路重读到读之后落下、还没有结果的认领（出现了 running 的 job）时，重算得出不成立、返回 False（ADR 0054
        决策二后台推进条「收尾与报告」：按继续推进处理）。要写时读到的写入序号不是整数抛 `RunStateUnreadable`、不写。重试用尽抛
        `RunStateWriteContended`。"""
        for attempt in range(_REPLACE_MAX_RETRIES + 1):
            self._back_off(attempt)
            item = self._read_state_item(run_id)
            if item is None:
                return False
            before = _run_state_from_item(item)
            after = ending_applied(before, ending, ended_at=ended_at)
            if after is None:
                return False
            if self._replace_state(run_id, item, before, after):
                return True
        raise RunStateWriteContended(self._table.name, run_id, _REPLACE_MAX_RETRIES + 1)

    # ---- 结束写的 error 变体：只写运行态的公共部分（ADR 0030 决定四「error 变体是另一个写入口」条、决定六「两个写入口的步骤」，
    # ADR 0031 决定三「结束写」小节「运行定义不可用、或 run 由别的格式写出时」条）。不在 RunStore 端口上，本机 adapter 没有它 ----

    def end_run_as_error(self, run_id: str, reason: str, *, ended_at: str) -> bool:
        """结束写的 error 变体：把每个未结束的 job 与 run 记为 error，原因与结束时刻由调用方给出。返回是否写成，写成即这次写使 run
        成为终态。只由云端推进器调用：运行定义不可用、或 run 由别的格式写出时（原因取 `run_status` 里的那几句之一）。

        不按本格式的模型解读运行态，也不经 `run_status.ending_applied`：同格式与别的格式写出的 run 都由它结束，所以只读公共部分（run
        级 status、jobs 各条目的 status）与写入序号，读到的条目原样复制，只改未结束的条目。每一轮的步骤：
        1. 强一致读整个 STATE。不存在即返回 False。公共部分读不出即抛 `RunStateUnreadable`、不写（缺状态分组不算读不出，ADR 0030
           决定六「runs 表只有一个 GSI」条）。run 已结束即返回 False、不写：记录保持先使 run 成为终态的那一方的结果。
        2. 一次 update_item：jobs 以读到的各条目整体替换，状态为 pending 或 running 的条目把 status 写成 error、message 写成 reason，条目
           里其余属性与已结束的条目原样复制；run 级 status 与状态分组写成 error，ended_at、message 写成调用方给的值，写入序号加一；STATE
           的其余属性不提及。条件与另两个整体替换的入口相同：写入序号等于读到的值且 run 未结束（`_conditional_replace`）。
        3. 条件不成立即重读、回到第 1 步，次数上限与另两个入口相同，用尽抛 `RunStateWriteContended`。超出单条记录大小上限之类不是条件
           不成立的错误原样抛出、不重读。"""
        for attempt in range(_REPLACE_MAX_RETRIES + 1):
            self._back_off(attempt)
            item = self._read_state_item(run_id)
            if item is None:
                return False
            run_status, jobs, seen_seq = self._common_part(run_id, item)
            if run_status not in _OPEN_STATUS_VALUES:
                return False
            replaced = {sid: ({**entry, "status": Status.ERROR.value, "message": reason}
                              if entry["status"] in _OPEN_STATUS_VALUES else entry)
                        for sid, entry in jobs.items()}
            run_set, run_names, run_values = _run_status_assignment(Status.ERROR)
            seq_set, seq_names, seq_values = _write_seq_increment()
            sets = ["jobs = :jobs", run_set, "ended_at = :e", "#msg = :m", seq_set]
            names = {**run_names, **seq_names, "#msg": "message"}
            values = {":jobs": replaced, ":e": ended_at, ":m": reason, ":pending": Status.PENDING.value,
                      ":running": Status.RUNNING.value, **run_values, **seq_values}
            if self._conditional_replace(run_id, seen_seq, sets, names, values):
                return True
        raise RunStateWriteContended(self._table.name, run_id, _REPLACE_MAX_RETRIES + 1)

    def _common_part(self, run_id: str, item: dict) -> tuple[str, dict, object]:
        """从读到的 STATE 里只取运行态的公共部分与写入序号（ADR 0037 决策 7「运行态的公共部分」）：返回（run 级 status, jobs Map,
        写入序号或 None）。读不出（run 级 status 不是七个状态值之一、jobs 不是 Map、某个条目不是 Map 或它的 status 不是七个状态值之一、
        写入序号在而不是整数值，见 `_seen_write_seq`）即抛 `RunStateUnreadable`。只核这几项：别的属性 error 变体原样复制、不解读。"""
        status = item.get("status")
        if not isinstance(status, str) or status not in _STATUS_VALUES:
            raise RunStateUnreadable(self._table.name, run_id, "run 级状态缺失或不是认得的状态值")
        jobs = item.get("jobs")
        if not isinstance(jobs, dict):
            raise RunStateUnreadable(self._table.name, run_id, "job 清单缺失或形态不对")
        for entry in jobs.values():
            entry_status = entry.get("status") if isinstance(entry, dict) else None
            if not isinstance(entry_status, str) or entry_status not in _STATUS_VALUES:
                raise RunStateUnreadable(self._table.name, run_id, "某个 job 的状态缺失或不是认得的状态值")
        return status, jobs, self._seen_write_seq(run_id, item)

    def _seen_write_seq(self, run_id: str, item: dict):
        """读到的 STATE 里的写入序号，三个整体替换 jobs 的写入口共用这一种读法：没有这个属性为 None（条件取「仍没有这个属性」）；有
        则须为整数值，否则抛 `RunStateUnreadable`。属性在而值为 null（DynamoDB 的 NULL 类型，读回同样是 None）按读不出处理、不当作
        缺属性，与 `_schema_version_attr` 区分缺键与 null 同一口径：对一个在而为 null 的属性，「仍没有这个属性」的条件永不成立，当作
        缺属性只会重读到次数用尽，把读不出的记录报成写入竞争。"""
        if _WRITE_SEQ_ATTR not in item:
            return None
        seq = item[_WRITE_SEQ_ATTR]
        if not _is_integral_number(seq):
            raise RunStateUnreadable(self._table.name, run_id, "写入序号不是整数")
        return seq

    @staticmethod
    def _back_off(attempt: int) -> None:
        """第 attempt 次写之前的等待：第一次（attempt 为 0）不等，此后按 `_REPLACE_BACKOFF_S` 翻倍。"""
        if attempt:
            time.sleep(_REPLACE_BACKOFF_S * 2 ** (attempt - 1))

    def _replace_state(self, run_id: str, seen: dict, before: RunState, after: RunState) -> bool:
        """一次条件写：把 STATE 从读到的 `before` 改成 `after`。写成返回 True；条件不成立返回 False，不改任何东西。

        写的内容：整体替换 jobs（不按 job 逐个写：逐个加条件的表达式随 job 数增长，ADR 0034 机制三②；每个条目带上它点名的标识，
        见 `_job_state_to_item`），run 状态连同状态分组（见 `status_group`；
        run 在这次写里成为终态时分组随之由 live 换成终态值），`after` 与 `before` 不同的结束时刻与 run 级说明，写入序号加一。其余属性
        （开始时刻、HWM、认领计数、顶层附加属性）不提及、原样保留，两个纯函数也不改它们。

        每个条目是 `seen` 里同一个 scope_id 的条目中不在已知键集内的属性，加上按 `after` 写出的模型键（ADR 0030 决定四「改写运行态时
        原样保留不认识的部分」条）。已知键不从读到的值并入：并入会把这次应当无值而省去的键按读到的旧值写回。

        条件：写入序号等于 `seen` 里读到的值（读到时没有这个属性即要求仍没有；读法见 `_seen_write_seq`），并且 run 未结束。前一项挡住
        读与写之间落下的、改变了 jobs 或 run 状态的写（这样的写都把序号加一）；后一项使「终态不可变」不只依赖每一次写都加了序号（ADR
        0054 决策五），它也挡住 STATE 已不在的情形。"""
        run_set, run_names, run_values = _run_status_assignment(after.status)
        seq_set, seq_names, seq_values = _write_seq_increment()
        sets = ["jobs = :jobs", run_set, seq_set]
        names = {**run_names, **seq_names}
        seen_jobs = seen.get("jobs") or {}
        jobs = {sid: {**_unknown_job_attrs(seen_jobs.get(sid)), **_job_state_to_item(js)} for sid, js in after.jobs.items()}
        values = {":jobs": jobs,
                  ":pending": Status.PENDING.value, ":running": Status.RUNNING.value, **run_values, **seq_values}
        if after.ended_at is not None and after.ended_at != before.ended_at:
            sets.append("ended_at = :e")
            values[":e"] = after.ended_at
        if after.message is not None and after.message != before.message:
            sets.append("#msg = :m")
            names["#msg"] = "message"
            values[":m"] = after.message
        return self._conditional_replace(run_id, self._seen_write_seq(run_id, seen), sets, names, values)

    def _conditional_replace(self, run_id: str, seen_seq, sets: list[str], names: dict, values: dict) -> bool:
        """整体替换 jobs 的三个写入口共用的那一次 update_item：在调用方给出的 SET 片段上加两项条件，写入序号等于读到的值 `seen_seq`
        （读到时没有这个属性即为 None，要求仍没有）且 run 未结束（ADR 0030 决定六「两个写入口的步骤」）。写成返回 True；条件不成立
        返回 False，不改任何东西；别的错误（如超出单条记录的大小上限）原样抛出、不重读。values 须已带 `:pending` 与 `:running`。"""
        if seen_seq is None:
            seq_condition = "attribute_not_exists(#ws)"
        else:
            seq_condition = "#ws = :seen"
            values = {**values, ":seen": seen_seq}
        try:
            self._table.update_item(
                Key={"run_id": run_id, _ITEM_TYPE_ATTR: _STATE},
                UpdateExpression="SET " + ", ".join(sets),
                ExpressionAttributeNames=names,
                ExpressionAttributeValues=values,
                ConditionExpression=f"#st IN (:pending, :running) AND {seq_condition}",
            )
            return True
        except self._table.meta.client.exceptions.ConditionalCheckFailedException:
            return False

    def _read_state_item(self, run_id: str) -> dict | None:
        """强一致读回整个 STATE item；不存在返回 None。"""
        return self._table.get_item(Key={"run_id": run_id, _ITEM_TYPE_ATTR: _STATE}, ConsistentRead=True).get("Item")

    def load_run_meta(self, run_id: str) -> RunMeta | None:
        """读整份运行定义（ADR 0030 决定六「云端提交记录」条的「读整份定义」一项）：强一致读头，按头里的 `jobs_ref` 取 jobs 对象，
        与 meta_json 拼回运行定义；头不在返回 None。没有注入 jobs 对象的存取即抛（装配缺失），先于任何读。

        结构版本先于取 jobs 对象核对：不是本读端认的即抛 `UnsupportedDefinitionSchema`，不取 jobs 对象。头缺 `jobs_ref`、meta_json 里
        另有 jobs、地址或 jobs 对象的内容形态不对，都是定义违约（`DefinitionContractError`）。取 jobs 对象的那一次读失败抛
        `JobsObjectUnreadable`（带错误种类，见 `jobs_object`），它不是定义违约：读端若把可重试的故障当定义违约，会把它永久记成 error。"""
        jobs_objects = self._require_jobs_objects()
        resp = self._table.get_item(Key={"run_id": run_id, _ITEM_TYPE_ATTR: _META}, ConsistentRead=True)
        item = resp.get("Item")
        if item is None:
            return None
        meta_dict = definition_from_json(item["meta_json"])
        require_definition_schema(meta_dict)
        if "jobs_ref" not in item:
            raise DefinitionContractError("提交记录的头缺 jobs_ref，找不到其中的 job 列表")
        if "jobs" in meta_dict:
            # job 列表只在 jobs 对象里：两处都有时不知道该信哪一份
            raise DefinitionContractError("提交记录的头里不应有 job 列表")
        meta_dict["jobs"] = jobs_objects.get(run_id, item["jobs_ref"])
        return run_meta_from_dict(meta_dict)

    def peek_definition_header(self, run_id: str) -> tuple[int, str | None] | None:
        """只取 META item 顶层的结构版本与写端 CLI 版本（ADR 0037 决策 7）；item 不存在返回 None，没有该属性读作 0。
        ProjectionExpression 只取两个属性：不拖回 meta_json、不取 jobs 对象，不要 jobs 对象的注入与产物桶的读权限。"""
        resp = self._table.get_item(
            Key={"run_id": run_id, _ITEM_TYPE_ATTR: _META},
            ConsistentRead=True,
            ProjectionExpression="#sv, #cv",
            ExpressionAttributeNames={"#sv": "schema_version", "#cv": "cli_version"},
        )
        item = resp.get("Item")
        if item is None:
            return None
        return _header_from_item(item)

    def load_run_state(self, run_id: str) -> RunState | None:
        """读回运行态（从 STATE item，jobs 原生 Map → dict[scope_id, JobState]）；不存在返回 None。

        ConsistentRead=True（ADR 0030 决定六「读用 ConsistentRead=True」条）：使 run 成为终态的那次写之后立刻读（组装 run 的结果、
        生成报告）要读到这次写。
        """
        item = self._read_state_item(run_id)
        if item is None:
            return None
        return _run_state_from_item(item)

    # ---- 列举（ADR 0041 决策七「云端实现」）----

    def list_runs(self, statuses: Sequence[Status], *, limit: int | None) -> list[RunListing]:
        """列举（语义见 RunStore port）：按状态分组 Query 索引（run_id 降序），run_id 先去重，再用 `BatchGetItem` 强一致读回每个
        run 的 STATE 与 META（同一批请求，不另起读取）。

        分组由 `status_group` 从所请求的状态算出：所请求的非终态都落在 `live` 分组，只查一次、最先查；所请求的终态各查同名的分组，
        按 `statuses` 的给定顺序。先查 `live` 与 CLI 两次调用的次序同一依据（ADR 0041 决策七「CLI 的合并」）：正常生命周期里
        run 只从 `live` 分组走向终态分组，先查 `live` 才不会漏掉两次查询之间收尾的 run。

        经 `live` 分组找到的行按读回的状态判定是否列出（端口「不按状态复筛」的例外）：读回为所请求的非终态的列出，读回为未被请求的
        非终态的不列出，读回已到终态的与无法读取的照常列出、不复筛。经所请求的终态分组找到的行不复筛，照常列出。

        `limit` 为 None 时每个分组分页读完，全部 run_id 收齐后一次读回。`limit` 给出时逐个分组按页补读：每页按还差的可读 run 条数
        取键、读回、解析，凑满或分组读完即停；其间遇到的无法读取的行照常列出、不占名额，读回时 STATE 已不在的行同样不占名额。
        `live` 分组按所请求的各非终态分别计名额：读回状态为某个所请求非终态的可读行计入该状态，该状态已凑满之后的同状态行不列出
        （与本机每个状态只取前 `limit` 条一致），读回已到终态的行列出、不计入任何非终态的名额；每页取的键数是各状态还差的条数之和，
        各状态都凑满或分组读完即停。终态分组里，前面分组已读回过的 run 不再读回，它在本分组是否占名额按已读回的结果定。

        行内容以读回的 STATE 为准；索引里有键而 STATE 已不在的行跳过（item 已删，索引尚未跟上）。STATE 解析不了（形态违约、run 级或
        job 状态值本版本不认识、清单要输出的字段类型不对）以 `state=None` 列出；detached 与 `is_detached` 同一判据（STATE 顶层标记）；
        头部与 `peek_definition_header` 同一读法，META 不在或头部解析不了（含写端版本不是字符串，如数值属性读回的 Decimal）为 None。
        Query 与读回的 AWS 错误原样抛出（索引缺失时 Query 以 ValidationException 失败）；读回的未处理键重试耗尽抛
        `RunListingIncomplete`。
        """
        if self._list_index_name is None:
            raise RuntimeError("本进程的 RunStore 没有配置列举 run 用的索引名，列不出 run"
                               "（配置缺失：起 RunStore 的地方须注入 list_index_name）")
        if limit is not None and limit < 1:
            raise ValueError(f"limit 须为正整数或 None，现为 {limit!r}")
        wanted = list(dict.fromkeys(statuses))
        live = [s for s in wanted if status_group(s) == _STATUS_GROUP_LIVE]
        ended_groups = [status_group(s) for s in wanted if status_group(s) != _STATUS_GROUP_LIVE]
        if limit is None:
            rows = self._list_unbounded(live, ended_groups)
        else:
            rows = self._list_bounded(live, ended_groups, limit)
        rows.sort(key=lambda row: row.run_id, reverse=True)
        return rows

    def _list_unbounded(self, live: list[Status], ended_groups: list[str]) -> list[RunListing]:
        """`limit` 为 None 的列举：各分组分页读完，run_id 去重后一次读回，经 `live` 分组找到的行按 `_listed_from_live` 判定。"""
        from_live = self._query_whole_group(_STATUS_GROUP_LIVE) if live else []
        from_ended = [run_id for group in ended_groups for run_id in self._query_whole_group(group)]
        via_ended = set(from_ended)
        # 先去重再读回：同一 run 可能在索引传播期间同时出现在新旧两个分组，而 BatchGetItem 的同一请求里出现重复的键，整个请求以
        # ValidationException 失败
        rows = self._read_listing_rows(list(dict.fromkeys(from_live + from_ended)))
        return [row for row in rows if row.run_id in via_ended or _listed_from_live(row, live)]

    def _list_bounded(self, live: list[Status], ended_groups: list[str], limit: int) -> list[RunListing]:
        """`limit` 给出的列举：逐个分组按页补读（名额规则见 `list_runs`）。"""
        seen: set[str] = set()  # 已读回过的 run_id（去重理由同 `_list_unbounded`）
        read: dict[str, RunListing] = {}  # 已读回的行；STATE 已不在的不在其中
        listed: dict[str, RunListing] = {}

        def read_page(group: str, want: int, start: dict | None) -> tuple[list[str], dict | None]:
            page, start = self._query_index_page(group, want, start)
            fresh = [run_id for run_id in page if run_id not in seen]
            seen.update(fresh)
            read.update((row.run_id, row) for row in self._read_listing_rows(fresh))
            return page, start

        if live:
            counted = dict.fromkeys(live, 0)  # 各所请求非终态已凑到的可读条数
            start = None
            while True:
                page, start = read_page(_STATUS_GROUP_LIVE, sum(limit - n for n in counted.values()), start)
                for run_id in page:
                    row = read.get(run_id)
                    if row is None or not _listed_from_live(row, live):
                        continue
                    if row.state is not None and row.state.status in counted:
                        if counted[row.state.status] >= limit:
                            continue  # 该状态已凑满：这一行排在它的前 limit 条之后，不列出
                        counted[row.state.status] += 1
                    listed[run_id] = row
                # 没有下一页即停：一页全是无法读取的行时也在这里结束，不因名额未满而反复查
                if start is None or all(n >= limit for n in counted.values()):
                    break
        for group in ended_groups:
            readable = 0
            start = None
            while True:
                page, start = read_page(group, limit - readable, start)
                for run_id in page:
                    row = read.get(run_id)
                    if row is None:
                        continue
                    listed[run_id] = row  # 经所请求的终态分组找到：不复筛，经 live 分组找到而未列出的这里同样列出
                    readable += row.state is not None
                if readable >= limit or start is None:
                    break
        return list(listed.values())

    def _query_whole_group(self, group: str) -> list[str]:
        """分页读完一个分组的 run_id（run_id 降序）。"""
        run_ids: list[str] = []
        start = None
        while True:
            page, start = self._query_index_page(group, None, start)
            run_ids.extend(page)
            if start is None:
                return run_ids

    def _read_listing_rows(self, run_ids: list[str]) -> list[RunListing]:
        """读回这些 run（须已去重）并解析成列举项，次序同 `run_ids`；STATE 已不在的 run 不出现。`run_ids` 为空时不发请求。"""
        items = self._batch_get_listing_items(run_ids)
        rows: list[RunListing] = []
        for run_id in run_ids:
            state_item = items.get((run_id, _STATE))
            if state_item is None:
                continue
            try:
                state = require_listing_state(_run_state_from_item(state_item))
            except UNREADABLE_RECORD_ERRORS:  # 形态违约、状态值不认识、字段类型不对
                state = None
            meta_item = items.get((run_id, _META))
            try:
                header = require_listing_header(_header_from_item(meta_item)) if meta_item is not None else None
            except ValueError:  # 结构版本不是整数、写端版本不是字符串（DefinitionContractError）：头部解析不了，与本机同读作 None
                header = None
            rows.append(RunListing(run_id=run_id, state=state, detached=bool(state_item.get("detached")), header=header))
        return rows

    def _query_index_page(self, group: str, limit: int | None, start: dict | None) -> tuple[list[str], dict | None]:
        """按 run_id 降序读一个状态分组的一页 run_id：`limit` 给出时这一页至多取这么多条（一页可能更少），`start` 是上一页给出的
        续读起点。返回这一页的 run_id 与下一页的起点，没有下一页时起点为 None。"""
        kwargs: dict = {
            "IndexName": self._list_index_name,
            "KeyConditionExpression": "#sg = :g",
            "ExpressionAttributeNames": {"#sg": _STATUS_GROUP_ATTR},
            "ExpressionAttributeValues": {":g": group},
            "ScanIndexForward": False,
        }
        if limit is not None:
            kwargs["Limit"] = limit
        if start is not None:
            kwargs["ExclusiveStartKey"] = start
        resp = self._table.query(**kwargs)
        # 没有游标与空字典游标都按已到末页处理：空字典不标明续读的起点，用它续查不能推进分页，可能反复读同一段而不结束
        return [item["run_id"] for item in resp.get("Items", [])], resp.get("LastEvaluatedKey") or None

    def _batch_get_listing_items(self, run_ids: list[str]) -> dict[tuple[str, str], dict]:
        """强一致读回这些 run 的 STATE 与 META item，返回 {(run_id, item_type): item}；不在的 item 不出现。

        `run_ids` 须已去重。每次请求至多 `_BATCH_GET_MAX_KEYS` 个键（每个 run 两个键）；返回的未处理键带退避重试，
        至多 `_BATCH_GET_MAX_RETRIES` 次，耗尽抛 `RunListingIncomplete`、不返回缺行的结果。
        """
        client = self._table.meta.client
        table_name = self._table.name
        names = {f"#a{i}": attr for i, attr in enumerate(_LISTING_ATTRS)}  # 全部走 names：status、message 等是保留字
        keys = [{"run_id": run_id, _ITEM_TYPE_ATTR: item_type} for run_id in run_ids for item_type in (_STATE, _META)]
        read_options = {"ConsistentRead": True, "ProjectionExpression": ", ".join(names), "ExpressionAttributeNames": names}
        got: dict[tuple[str, str], dict] = {}
        for start in range(0, len(keys), _BATCH_GET_MAX_KEYS):
            batch = keys[start:start + _BATCH_GET_MAX_KEYS]
            for attempt in range(_BATCH_GET_MAX_RETRIES + 1):
                resp = client.batch_get_item(RequestItems={table_name: {"Keys": batch, **read_options}})
                for item in resp.get("Responses", {}).get(table_name, []):
                    got[(item["run_id"], item[_ITEM_TYPE_ATTR])] = item
                # 重试只发未处理的键，读取选项每次重新带上（强一致与投影不依赖响应里是否回带）
                batch = ((resp.get("UnprocessedKeys") or {}).get(table_name) or {}).get("Keys") or []
                if not batch:
                    break
                if attempt == _BATCH_GET_MAX_RETRIES:
                    # 没读回的 run 包括这一批剩下的与因此不再发出的后续各批里的（一个 run 只要有一个键没读回就计入）
                    unread = {k["run_id"] for k in batch} | {k["run_id"] for k in keys[start + _BATCH_GET_MAX_KEYS:]}
                    raise RunListingIncomplete(table_name, len(unread), _BATCH_GET_MAX_RETRIES)
                time.sleep(_BATCH_GET_BACKOFF_S * 2 ** attempt)
        return got

    def is_detached(self, run_id: str) -> bool:
        """STATE item 上有没有 `detached` 标记（ADR 0034）：True 表示无状态批量运行的 submit 建的 run。

        **adapter-only 只读访问器、不在 RunStore port 上**——detached 是执行环境属性、不进 core 模型
        （ADR 0034 端到端 cloud 1b「触发过滤不看后台执行标记」），只有云端推进器组合根需要它做「只推进 detached run」的
        分流：同步 `run --backend cloud` 由进程内 schedule 推进，推进器碰它即双开推进器。
        STATE 缺失 → False（保守不推进；`create_run` 的写序 META→STATE 保证 detached run 被触发时 STATE 已在）。
        ProjectionExpression 只取标记（不拖回可能很大的 jobs Map）；`#d` 走 names 以防 DDB 保留字。
        """
        resp = self._table.get_item(
            Key={"run_id": run_id, _ITEM_TYPE_ATTR: _STATE},
            ConsistentRead=True,
            ProjectionExpression="#d",
            ExpressionAttributeNames={"#d": "detached"},
        )
        return bool((resp.get("Item") or {}).get("detached"))
