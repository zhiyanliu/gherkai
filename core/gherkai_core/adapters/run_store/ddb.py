"""DynamoDBRunStore（ADR 0030 决定六）：RunStore port 的 DynamoDB 实装。

对拍 `LocalRunStore` 的行为（同一批 round-trip/生命周期/报错语义），只换落点为 DDB。**云端 adapter，需 boto3**
（`gherkai-core[aws]` optional extra，缺它 import 本模块不崩、构造时才友好报错，守 [0016] 窄腰）。

表 schema（决定六）：单表、分区键字段 `run_id` + 排序键字段 `item_type`（取值 `'META'`/`'STATE'`）——
RunMeta 与 RunState **分两 item**（同 run_id、item_type 各异；同分区键下一次 Query 可原子捞回该 run 全部）：
- **META item**：`{run_id, item_type='META', schema_version, cli_version, deadline_at, meta_json=<json.dumps(run_meta_to_dict)>}`
  （三个顶层属性是 meta_json 里同名键的摊出副本，见 `create_run`）。RunMeta 是 definition，
  **write-once（create_run）/ read-whole（load_run_meta）**，从不单元素更新——故整体存 JSON 字符串最简、
  且躲开 DDB 原生 Map 对空串/嵌套 list 的挑剔（DataTable rows 常含空 cell）。StepArgument offload（同包 `arg_offload.py`，ADR 0030 决定六）在 `json.dumps`
  **前**对 dict 里的 docString/dataTable 换指针，不需要 META 是原生 Map。
- **STATE item**：`{run_id, item_type='STATE', status, status_group, started_at?, ended_at?, high_water_mark?, message?,
  claim_count, write_seq, jobs=<原生 Map>}`（`?` = omit-when-None；`message` 是 run 级说明，随 try_finalize 或结束写 `end_run` 写入；
  `high_water_mark` 与 `claim_count` 是本 item 的两个数值属性，读回 Decimal 转 int——前者只在无状态批量运行的投影写时有值，投影写的
  ConditionExpression 按它做数值守卫，见 ADR 0034 机制三；后者是认领计数，create_run 恒写、认领成功时原子加一、缺属性读作 0，
  见 ADR 0034 机制三「run 级状态只进不退」条①；`write_seq` 是写入序号，见 `_write_seq_increment`；`status_group` 是由
  run 级 `status` 派生的状态分组、状态分组索引的分区键，写入规则见 `status_group`），另有两个
  **可选顶层标记**：`detached`（kicker 的 Stream filter 认它）与 `worker_task_def_arns`（ADR 0038，
  清理 pass 的运行中 run 引用检查经状态分组索引读 `live` 分组里各 run 的这个属性）——两者都是「DDB 侧要查得动」才摊到顶层的。
  这类顶层附加属性只在 create_run 时写下；之后的写全是 update_item，不提及的属性原样保留。
  jobs **必须原生 Map** 才能 `SET jobs.#sid=:js` 按 scope_id 单元素刷；其 entry 全是 str（无 float），
  原生 Map 无 Decimal 顾虑。jobs 的写法有两种：认领、投影与 `update_job_state` 按 scope_id 写单个 job 或它的属性；
  `commit_job_states` 与 `end_run` 以写入序号为条件整体替换 jobs，替换的内容由读到的运行态算出（ADR 0034 机制三②）。

字段仍源于 `serialize`（单一真理源）：META 直接 `json.dumps(run_meta_to_dict)`；STATE 的标量 + jobs 各 entry
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
from gherkai_core.adapters.run_store.arg_offload import has_pointers
from gherkai_core.model import TERMINAL_STATUSES, JobState, RunListing, RunMeta, RunState, Status
from gherkai_core.run_status import CommitOutcome, RunEnding, check_running_write, commit_applied, ending_applied
from gherkai_core.serialize import (
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
    `_state_scalars`，update_item 经 `_run_status_assignment`）；不写 run 级 `status` 的写（全 pending 的投影、投影的逐 job 写）
    不碰分组属性，写之前缺它的记录写之后仍缺。分组只服务这个索引；本机后端没有索引，不写它。
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
    """update_item 里把写入序号加一的 SET 片段：本 adapter 写 STATE 的每一次 update_item 都带上它（create_run 写初值 0）。

    整体替换 jobs 的两个写入口（`commit_job_states`、`end_run`）只以「序号等于读到的值」为条件，所以别的写不论改了什么都要让序号
    变化：一次不加一的写若落在整体替换的读与写之间，就会被那次整体替换盖掉（ADR 0034 机制三②）。缺属性按 0 起算（`if_not_exists`，
    同认领计数）。返回（片段, ExpressionAttributeNames, ExpressionAttributeValues），占位名 `#ws`、占位值 `:ws0` / `:ws1` 不与各调用方
    重名。"""
    return ("#ws = if_not_exists(#ws, :ws0) + :ws1", {"#ws": _WRITE_SEQ_ATTR}, {":ws0": 0, ":ws1": 1})


# 整体替换 jobs 的两个写入口条件不成立时重读再算（ADR 0034 机制三②）：每次条件不成立都说明读与写之间有别的写落下。至多重试
# _REPLACE_MAX_RETRIES 次，第 k 次重试之前等 _REPLACE_BACKOFF_S * 2 ** (k - 1) 秒：并发的投影按 job 逐个写、每次都让序号加一，
# 一个 job 多的 run 上它持续的时间可能长于一次读与写，退避让这次写在它写完之后再读。全部重试用尽约等十秒，仍不成立即抛
# `RunStateWriteContended`。
_REPLACE_MAX_RETRIES = 10
_REPLACE_BACKOFF_S = 0.01


class RunStateWriteContended(RuntimeError):
    """`commit_job_states` 或 `end_run` 重读再算的次数用尽，每一次都被读与写之间落下的别的写挡下：这次没有写成，运行态不因它改变。
    调用方按写不进运行态处理（与存储不可达同类）。`table` 是 runs 表名，`run_id` 是这个 run，`attempts` 是写的次数。"""

    def __init__(self, table: str, run_id: str, attempts: int) -> None:
        super().__init__(f"写入运行状态表 {table} 里 run {run_id} 的状态时，连续 {attempts} 次都有同时进行的其他写入先落下，"
                         "这次没有写成；请稍后重试。")
        self.table = table
        self.run_id = run_id
        self.attempts = attempts


# 列举的读回（ADR 0041 决策七「云端实现」）：BatchGetItem 每次请求至多 100 个键（DynamoDB 服务限额）；返回的未处理键带退避
# 重试、次数有界，首次重试前等 _BATCH_GET_BACKOFF_S 秒、之后每次翻倍。
_BATCH_GET_MAX_KEYS = 100
_BATCH_GET_MAX_RETRIES = 5
_BATCH_GET_BACKOFF_S = 0.05
# 读回只取运行态、detached 标记与头部要用的属性：META 的 meta_json 可达数百 KB，整批拖回会让单次响应超出大小上限、变成更多
# 未处理键；worker_task_def_arns 只服务清理的引用检查。投影只减少传回的数据，读量仍按整个 item 计。
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


def _job_state_to_item(js: JobState) -> dict:
    """JobState → DDB Map entry（字段集同 serialize；session_id、claimed_at 与 job 级说明 message 用 omit-when-None，读回 .get 得
    None，ADR 0030 决定五、决定六）。"""
    d: dict = {"status": js.status.value}
    if js.session_id is not None:
        d["session_id"] = js.session_id
    if js.claimed_at is not None:
        d["claimed_at"] = js.claimed_at
    if js.message is not None:
        d["message"] = js.message
    return d


def _job_state_from_item(scope_id: str, m: dict) -> JobState:
    return JobState(scope_id=scope_id, status=Status(m["status"]),
                    session_id=m.get("session_id"), claimed_at=m.get("claimed_at"), message=m.get("message"))


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

    def __init__(self, table, arg_offloader=None, *, detached: bool = False,
                 list_index_name: str | None = None) -> None:
        """table：boto3 dynamodb.Table 资源（组合根注入；建表责任在 IaC，adapter 假定已存在）。

        arg_offloader：可选 S3StepArgumentOffloader（ADR 0030 决定六）。注入则 RunMeta 深树里的
        docString/dataTable 正文搬 S3、META item 只留指针（解 DDB 400KB 限）；None（默认）则 argument
        原样内联进 meta_json（小 run / 单测省一层 S3）。只挂 RunMeta 写/读路径，RunState 无 argument、不涉及。

        detached：本组合根是否「无状态批量运行的 submit」——True 则 create_run 的 STATE item 带
        `detached=true` 顶层标记，kicker Lambda 的 Stream filter 只认它（同步 `run --backend cloud` 的
        create_run 无此标记、不触发 kicker——否则双开推进器、重复起 task）。执行环境属性、不进 core 模型。

        list_index_name：列举用的状态分组索引名（ADR 0041 决策七；命名真源在 runtime，组合根注入）。只有 `list_runs` 用它；
        None（默认）时其余方法照常，调用 `list_runs` 即抛错（装配缺失）。就绪与否由组合根在装配时核，本 adapter 不查。
        """
        require_boto3("DynamoDBRunStore")
        self._table = table
        self._arg_offloader = arg_offloader
        self._detached = detached
        self._list_index_name = list_index_name

    # ---- 生命周期写入口（ADR 0030 决定六）----

    def create_run(self, meta: RunMeta, initial_state: RunState) -> None:
        """run 开始：写 META（definition，JSON 字符串）+ STATE（初始运行态，jobs 原生 Map）两 item，只在 run 不存在时成立。

        **写序 META→STATE 是契约**（ADR 0034）：kicker 由 STATE 的 INSERT 触发（detached 标记在 STATE 上），
        触发时 META 必已在——若标 META，kicker 可能在 STATE 落库前 tick、claim/投影全 CCF 空转。

        **建 run 是条件写**（ADR 0054 决策五）：已存在即抛 FileExistsError，不改任何东西。两道检查：
        1. 卸载 step 参数正文之前，以强一致读确认这个 run_id 下 META 与 STATE 都不存在（只取主键，不拖回 meta_json），任一已在
           即失败——已卸载到 S3 的正文不被重写。读用 GetItem，与 `status` 读运行态同一个动作。
        2. 两次 put 都带「条目不存在」的条件，任一被挡即失败。
        已知边界：第 1 道检查的读与第 2 道检查的写之间另一方建了同一个 run_id 时，条目仍只有一方写成（第 2 道检查挡住），
        但 S3 里的正文可能已被本方重写。run_id 由发起进程新生成、带随机尾，这个窗口不另设机制防护。"""
        run_id = meta.run_id
        for item_type in (_META, _STATE):
            resp = self._table.get_item(
                Key={"run_id": run_id, _ITEM_TYPE_ATTR: item_type},
                ConsistentRead=True,
                ProjectionExpression="#rid",
                ExpressionAttributeNames={"#rid": "run_id"},
            )
            if "Item" in resp:
                raise FileExistsError(f"run {run_id} 已存在，不重新建立")
        meta_dict = run_meta_to_dict(meta)
        if self._arg_offloader is not None:
            # docString/dataTable 正文搬 S3、META 只留指针（解 DDB 400KB 限，ADR 0030 决定六）
            meta_dict = self._arg_offloader.offload(meta_dict, run_id)
        ccf = self._table.meta.client.exceptions.ConditionalCheckFailedException
        try:
            self._table.put_item(Item={
                "run_id": run_id,
                _ITEM_TYPE_ATTR: _META,
                # 结构版本与写端版本摊成顶层属性（ADR 0037 决策 7）：status / explain 与 list-runs 用投影只取这两个值、不解析
                # meta_json、不触发卸载正文的 S3 取回；运行期限同样摊出（ADR 0054 决策二），读它的一方不必取回整份 definition。
                # 三者的值与 meta_json 里的同名键恒同（同一份 meta_dict）。
                "schema_version": meta_dict["schema_version"],
                "cli_version": meta_dict["cli_version"],
                "deadline_at": meta_dict["deadline_at"],
                "meta_json": json.dumps(meta_dict, ensure_ascii=False),
            }, ConditionExpression="attribute_not_exists(run_id)")
            self._table.put_item(Item=self._state_item(meta, initial_state),
                                 ConditionExpression="attribute_not_exists(run_id)")
        except ccf as e:
            raise FileExistsError(f"run {run_id} 已存在，不重新建立") from e

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
            _WRITE_SEQ_ATTR: 0,  # 之后每次 update_item 加一（见 `_write_seq_increment`）
            "jobs": {sid: _job_state_to_item(js) for sid, js in initial_state.jobs.items()},
        }

    def update_job_state(self, run_id: str, job_state: JobState) -> bool:
        """执行中的写（语义见 RunStore port）：按 scope_id 整项替换 STATE.jobs 里的一个条目（SET jobs.#sid=:js），只发**一次**
        update_item。写入的不是 running 即抛 ValueError（`run_status.check_running_write`），不发写。

        #sid 用 ExpressionAttributeNames 承载任意 scope_id（含 / : 中文，绕开保留字/特殊字符）。

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
        try:
            self._table.update_item(
                Key={"run_id": run_id, _ITEM_TYPE_ATTR: _STATE},
                UpdateExpression=f"SET jobs.#sid = :js, {run_set}, {seq_set}",
                # status 是 DDB 保留字；jobs.#sid.#st 与 run 级同名，共用占位名
                ExpressionAttributeNames={"#sid": job_state.scope_id, **run_names, **seq_names},
                ExpressionAttributeValues={":js": _job_state_to_item(job_state), ":pending": Status.PENDING.value,
                                           ":running": Status.RUNNING.value, **run_values, **seq_values},
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
        """HWM 条件写 STATE：仅当 (传入 hwm ≥ 库中 hwm) 且 (库中 run 未结束) 才写（机制三①）。CCF → stale/已终态 → False。

        **run 级 status 只写 running、不落终态**（run 级终态只随记下最后一个 job 终态的写或结束写写下；投影提前落终态，那两次写会
        读到 run 已结束而写不成）。
        取值规则见 `projected_run_status`（与 local adapter 共用一份）：它给出 running 时标量写带上 run 级；给出 pending
        （投影里全 job 仍 pending）时更新表达式省略 run 级、只写 HWM，库中 run 级原样保留，认领或此前投影已写成的 running
        不被拿着旧 baseline 的投影改回 pending。条件双守不变：
        HWM 挡 stale + status 挡「已结束被刷回」。run 级只在这次带终态守卫的标量写里落，逐 job 阶段不写 run 级。

        **各 job 态逐 job 单调条件写（对拍 local 的逐 job 合并）**：task_exited 无数值
        seq，两次投影可携带相同 HWM、①挡不住 job 终态被 stale 投影刷回（还会重开 double-launch 窗口，机制四）。
        DDB put_item 表达不了 per-key 条件 → 拆两步：先 update_item 条件写标量（HWM+status 双守，CCF 即整体
        stale 返 False），再对每个 job（无效果的 pending 项除外，见末段）**逐属性** `SET jobs.#sid.status/.session_id/.claimed_at`
        + 「当前非更推进态」的单元素条件写，被挡的单个 job 静默跳过（库中已更推进，正确态在库、无信息丢失）。库中已是终态的 job
        不被改写（终态只写一次，ADR 0031 决定一·补）：写终态与写 running 的两支都以库中这个 job 为 pending 或 running 为条件；三支都
        另以 run 未结束为条件，所以终态写或结束写落在标量一步与逐 job 写之间时，余下的逐 job 写都写不成（ADR 0054 决策五）。
        逐属性而非整 entry：update_item 不碰未提及属性，投影没带的 session_id/claimed_at（claimed_at 只由 try_claim_job
        落库、事件推演不出）天然保留——对拍 local 的「投影缺字段回填库中值」兜底，不再依赖调用方总传 baseline。
        两步非原子，但每步各自条件守卫、次序（先标量后 jobs）保证中间态只会「标量新、job 旧」，等价于一次携带旧 job
        视图的合法投影，下轮重放收敛。
        update_item 天然不碰未提及属性——传入的 started_at、ended_at、message 都不写，库中值保留（started_at 由 create_run
        落；修「put_item 整 item 覆盖把 started_at 抹掉」的对拍不一致，local 同样只写 HWM、run 级与 jobs）。

        **无效果的 pending 项不发写**（ADR 0034 机制三「逐 job 写跳过无效果的 pending 项」段）：投影里 status 为 pending、
        session_id 与 claimed_at 都为空的 job 跳过。这类写只把 status 设为 pending，条件是库中该 job 为 pending：库中为 pending
        时写入值与库中值相同；库中已 running 或终态、或该 job 不在 Map 里时条件不成立、写被挡下。两种情形库中都不变，跳过与否
        结果相同，与调用方是否传 baseline 无关；而每次写都按整个 STATE item 的大小计费。三个条件缺一不可：投影一旦带了会话或
        认领时刻，这次写就可能改变库中值，照常发出。local 不需要同样跳过（锁内整份写回一次，写入次数不随 job 数增长）。

        标量一步与每一次逐 job 写都把写入序号加一（见 `_write_seq_increment`）。"""
        from gherkai_core.project import _lifecycle_rank, projected_run_status

        new_hwm = state.high_water_mark or 0
        seq_set, seq_names, seq_values = _write_seq_increment()
        # run 级 status 按投影里的 job 态定（全 pending → 不写，否则 running）；传入的 run 级值在有 job
        # 出判定时即为终态聚合值，一律不用（规则与理由见 projected_run_status）。此处读不到库中 job 态（下面 per-job 条件写
        # 才碰它们），判据只看投影——与 local 同一规则、可对拍。
        # 写 run 级时连同状态分组（见 `status_group`）；全 pending 不写 run 级，分组也不碰
        update, names, values = "SET high_water_mark = :h, " + seq_set, {"#st": "status", **seq_names}, {
            ":h": new_hwm, ":pending": Status.PENDING.value, ":running": Status.RUNNING.value, **seq_values}
        if projected_run_status(state.jobs) == Status.RUNNING:
            run_set, run_names, run_values = _run_status_assignment(Status.RUNNING)
            update += ", " + run_set
            names.update(run_names)
            values.update(run_values)
        try:
            self._table.update_item(
                Key={"run_id": run_id, _ITEM_TYPE_ATTR: _STATE},
                UpdateExpression=update,
                # (库中无 hwm 或 hwm ≤ 我的) 且 库中 status 仍非终态 → 允许；否则 CCF（stale / 已 finalize）
                ConditionExpression=(
                    "(attribute_not_exists(high_water_mark) OR high_water_mark <= :h) "
                    "AND #st IN (:pending, :running)"
                ),
                ExpressionAttributeNames=names,
                ExpressionAttributeValues=values,
            )
        except self._table.meta.client.exceptions.ConditionalCheckFailedException:
            return False
        # job 级：逐 job 单调条件写。rank 序 pending(0)<running(1)<终态(2)：仅当库中该 job 未结束、且 rank 不高于本次投影才写
        # （running 刷 running 取本次投影的值；库中已是终态的不改）。每一支都另以 run 未结束为条件（#jst 同指 run 级的 status）。
        run_open = "#jst IN (:pending, :running)"
        for sid, js in state.jobs.items():
            if js.status == Status.PENDING and js.session_id is None and js.claimed_at is None:
                continue  # 无效果的 pending 项不发写（等价性论证见 docstring 末段）
            new_rank = _lifecycle_rank(js.status)
            try:
                if new_rank >= 1:
                    # 写 running 或终态：库中这个 job 须为 pending 或 running。job 不在 Map 里时条件同样不成立（不臆造 job，与
                    # local 同样静默跳过；逐属性 SET 的父路径不存在会 ValidationException，条件先把它挡成 CCF）
                    cond = f"jobs.#sid.#jst IN (:pending, :running) AND {run_open}"
                else:
                    cond = f"jobs.#sid.#jst = :pending AND {run_open}"
                vals = {":pending": Status.PENDING.value, ":running": Status.RUNNING.value}
                sets = ["jobs.#sid.#jst = :st", seq_set]
                vals[":st"] = js.status.value
                vals.update(seq_values)
                if js.session_id is not None:  # omit-when-None 即不提及，也就是保留库中值（回填兜底）
                    sets.append("jobs.#sid.session_id = :sess")
                    vals[":sess"] = js.session_id
                if js.claimed_at is not None:
                    sets.append("jobs.#sid.claimed_at = :cat")
                    vals[":cat"] = js.claimed_at
                self._table.update_item(
                    Key={"run_id": run_id, _ITEM_TYPE_ATTR: _STATE},
                    UpdateExpression="SET " + ", ".join(sets),
                    ExpressionAttributeNames={"#sid": sid, "#jst": "status", **seq_names},
                    ExpressionAttributeValues=vals,
                    ConditionExpression=cond,  # 三分支一律带条件
                )
            except self._table.meta.client.exceptions.ConditionalCheckFailedException:
                continue  # 库中该 job 已结束或更推进（已 claim），或 run 已结束 → 保留库中态，不回退
        return True

    def try_finalize(self, run_id: str, status: Status, ended_at: str, *, message: str | None = None,
                     expected_claim_count: int | None = None) -> bool:
        """状态机单调条件写：仅当总 status 是 pending 或 running 才写终态（commit 恰一次）。CCF → 已终态或 STATE 不存在
        → False。message（run 级消息，ADR 0037 决策 7）与终态同一次 update_item 写入；None 时不提及该属性、库中值保留（local 对拍）。
        状态分组同样在这次写里改为该终态的值（见 `status_group`）。

        expected_claim_count 给出时进条件表达式：库中认领计数等于它才写。期望为 0 时缺属性同样
        成立（与读端缺属性读作 0、local 的锁内重读对拍）。为 None 时条件不提计数。写入序号在这次写里加一（见 `_write_seq_increment`）。

        调用方见 `RunStore.try_finalize`；ADR 0030 决定四的写入口里没有它。"""
        run_set, run_names, run_values = _run_status_assignment(status)
        seq_set, seq_names, seq_values = _write_seq_increment()
        update = "SET " + run_set + ", ended_at = :e, " + seq_set
        names = {**run_names, **seq_names}  # status 是 DDB 保留字；message 走 names 以防同类
        values = {**run_values, ":e": ended_at, ":pending": Status.PENDING.value, ":running": Status.RUNNING.value,
                  **seq_values}
        condition = "#st IN (:pending, :running)"  # 仅非终态可迁；已终态 → CCF（幂等）
        if message is not None:
            update += ", #msg = :m"
            names["#msg"] = "message"
            values[":m"] = message
        if expected_claim_count is not None:
            names["#cc"] = "claim_count"
            values[":ecc"] = expected_claim_count
            if expected_claim_count == 0:
                condition += " AND (attribute_not_exists(#cc) OR #cc = :ecc)"
            else:
                condition += " AND #cc = :ecc"
        try:
            self._table.update_item(
                Key={"run_id": run_id, _ITEM_TYPE_ATTR: _STATE},
                UpdateExpression=update,
                ExpressionAttributeNames=names,
                ExpressionAttributeValues=values,
                ConditionExpression=condition,
            )
            return True
        except self._table.meta.client.exceptions.ConditionalCheckFailedException:
            return False

    # ---- run 的状态只由 job 的终态算出（ADR 0031 决定三）：两个写入口的作用由 run_status 给出，这里只负责读、写的条件与重试 ----
    # 两者的步骤相同：强一致读 STATE，按 run_status 的纯函数从读到的运行态算出要写下的运行态，再以「写入序号等于读到的值、run 未结束」
    # 为条件整体替换 jobs 并写下 run 状态（连同状态分组）；条件不成立即重读再算（ADR 0034 机制三②），次数上限见 `_REPLACE_MAX_RETRIES`。

    def commit_job_states(self, run_id: str, job_states: Sequence[JobState], *, ended_at: str) -> CommitOutcome:
        """带结果的 job 终态写（语义见 RunStore port）：每一轮按读到的运行态经 `run_status.commit_applied` 算出这次写的作用与结果。

        run 已结束（ALREADY_ENDED）时不写；给出的 job 在库中都已是终态时运行态不变，同样不写、返回 OPEN。否则发一次条件写（见
        `_replace_state`），写成即返回这一轮算出的结果，被挡下即重读再算：重读到 run 已结束返回 ALREADY_ENDED。每一轮都按这一轮读到的
        条目合并给出的 job（规则见 `run_status.commit_applied`）：读与写之间别的写为它写下的认领时刻在重读之后留下，写下的会话只在给出的
        job 没有会话时留下，两者都不被空值覆盖。读不到 STATE 抛 FileNotFoundError；参数不合要求时 commit_applied 在任何写之前抛
        ValueError。重试用尽抛 `RunStateWriteContended`。"""
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
        决策二后台推进条「收尾与报告」：按继续推进处理）。重试用尽抛 `RunStateWriteContended`。"""
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

    @staticmethod
    def _back_off(attempt: int) -> None:
        """第 attempt 次写之前的等待：第一次（attempt 为 0）不等，此后按 `_REPLACE_BACKOFF_S` 翻倍。"""
        if attempt:
            time.sleep(_REPLACE_BACKOFF_S * 2 ** (attempt - 1))

    def _replace_state(self, run_id: str, seen: dict, before: RunState, after: RunState) -> bool:
        """一次条件写：把 STATE 从读到的 `before` 改成 `after`。写成返回 True；条件不成立返回 False，不改任何东西。

        写的内容：整体替换 jobs（不按 job 逐个写：逐个加条件的表达式随 job 数增长，ADR 0034 机制三②），run 状态连同状态分组（见 `status_group`；
        run 在这次写里成为终态时分组随之由 live 换成终态值），`after` 与 `before` 不同的结束时刻与 run 级说明，写入序号加一。其余属性
        （开始时刻、HWM、认领计数、顶层附加属性）不提及、原样保留，两个纯函数也不改它们。

        条件：写入序号等于 `seen` 里读到的值（读到时没有这个属性即要求仍没有），并且 run 未结束。前一项挡住读与写之间落下的任何写
        （每次写都把序号加一）；后一项使「终态不可变」不只依赖每一次写都加了序号（ADR 0054 决策五），它也挡住 STATE 已不在的情形。"""
        run_set, run_names, run_values = _run_status_assignment(after.status)
        seq_set, seq_names, seq_values = _write_seq_increment()
        sets = ["jobs = :jobs", run_set, seq_set]
        names = {**run_names, **seq_names}
        values = {":jobs": {sid: _job_state_to_item(js) for sid, js in after.jobs.items()},
                  ":pending": Status.PENDING.value, ":running": Status.RUNNING.value, **run_values, **seq_values}
        if after.ended_at is not None and after.ended_at != before.ended_at:
            sets.append("ended_at = :e")
            values[":e"] = after.ended_at
        if after.message is not None and after.message != before.message:
            sets.append("#msg = :m")
            names["#msg"] = "message"
            values[":m"] = after.message
        seen_seq = seen.get(_WRITE_SEQ_ATTR)
        if seen_seq is None:
            seq_condition = "attribute_not_exists(#ws)"
        else:
            seq_condition = "#ws = :seen"
            values[":seen"] = seen_seq
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
        """读回 definition（从 META item 的 meta_json）；不存在返回 None。"""
        resp = self._table.get_item(Key={"run_id": run_id, _ITEM_TYPE_ATTR: _META}, ConsistentRead=True)
        item = resp.get("Item")
        if item is None:
            return None
        meta_dict = json.loads(item["meta_json"])
        # 结构版本先于一切（ADR 0037 决策 7）：参数还原要按本版本认的形状遍历 definition，别的版本写出的 META 可能让它先抛 KeyError，
        # 把「版本不合」变成一个裸异常、绕过调用方按 UnsupportedDefinitionSchema 的处置。
        require_definition_schema(meta_dict)
        if self._arg_offloader is not None:
            # content_ref/rows_ref 取回、消解回内联，再交 serialize（对 core 透明，ADR 0030 决定六）。遍历途中的形状错由 offloader
            # 翻成 DefinitionContractError（同版本下的定义违约）；S3 取回失败与装配错误（句柄类型不对）原样上抛——它们不是 definition
            # 的问题，读端若把它们当定义违约，会把一个可重试的故障永久标成 error
            meta_dict = self._arg_offloader.restore(meta_dict, run_id)
        elif has_pointers(meta_dict):
            # fail-loud（ADR 0030 决定七「不给生产选要不要正确」）：META 含 offload 指针而本实例没注入
            # offloader 属组合根装配错误（曾发生：Lambda 组合根漏注入 → 正文静默还原成 None、worker 拿
            # 空参数执行出错）。宁可报错，也不静默降级。判据走 arg_offload 的**位置遍历**（与 restore 同源，决定六
            # 「位置区分、非值探测」）——对 meta_json 原始串做 '"content_ref"' 子串 sniff 会被「正文恰为
            # 该串」的 docString/dataTable cell 误命中，把好 run 判成装配错误、读不回来。
            raise RuntimeError(
                f"run {run_id} 的 step 参数有外置副本，但本进程的 RunStore 读不回来"
                "（配置缺失：起 RunStore 的地方须注入 arg_offloader）")
        return run_meta_from_dict(meta_dict)

    def peek_definition_header(self, run_id: str) -> tuple[int, str | None] | None:
        """只取 META item 顶层的结构版本与写端 CLI 版本（ADR 0037 决策 7）；item 不存在返回 None，没有该属性读作 0。
        ProjectionExpression 只取两个属性：不拖回 meta_json、不碰 S3 卸载正文（status 的权限面与开销不变）。"""
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
            except (ValueError, KeyError, TypeError, AttributeError):  # 形态违约、状态值不认识、字段类型不对
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
