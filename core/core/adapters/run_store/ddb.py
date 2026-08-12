"""DynamoDBRunStore（ADR 0030 决定六）：RunStore port 的 DynamoDB 实装。

对拍 `LocalRunStore` 的行为（同一批 round-trip/生命周期/报错语义），只换落点为 DDB。**云端 adapter，需 boto3**
（`core[aws]` optional extra，缺它 import 本模块不崩、构造时才友好报错，守 [0016] 窄腰）。

表 schema（决定六）：单表、分区键字段 `run_id` + 排序键字段 `item_type`（取值 `'META'`/`'STATE'`）——
RunMeta 与 RunState **分两 item**（同 run_id、item_type 各异；同分区键下一次 Query 可原子捞回该 run 全部）：
- **META item**：`{run_id, item_type='META', meta_json=<json.dumps(run_meta_to_dict)>}`。RunMeta 是 definition，
  **write-once（create_run）/ read-whole（load_run_meta）**，从不单元素更新——故整体存 JSON 字符串最简、
  且躲开 DDB 原生 Map 对空串/嵌套 list 的挑剔（DataTable rows 常含空 cell）。第 4 步 offload 在 `json.dumps`
  **前**对 dict 里的 docString/dataTable 换指针，不需要 META 是原生 Map。
- **STATE item**：`{run_id, item_type='STATE', status, started_at?, ended_at?, jobs=<原生 Map>}`。jobs **必须原生 Map**
  才能 `SET jobs.#sid=:js` 按 scope_id 单元素刷（决定六）；其 entry 全是 str（无 float），原生 Map 无 Decimal 顾虑。

字段仍源于 `serialize`（单一真理源）：META 直接 `json.dumps(run_meta_to_dict)`；STATE 的标量 + jobs 各 entry
的字段集取自 `run_state_to_dict`，只是 jobs 的**容器形状**在本 adapter 从 list 特化成 Map（非第二真理源）。

建表责任在 IaC/组合根、非本 adapter——adapter 假定表已存在（决定六；测试由 conftest fixture 建表）。
"""
from __future__ import annotations

import json

from core.adapters._boto import require_boto3
from core.model import JobState, RunMeta, RunState, Status
from core.serialize import (
    run_meta_from_dict,
    run_meta_to_dict,
)

# 排序键字段名（区分同一 run 的 definition/运行态 item，见决定六）——用 item_type 不用缩写 sk
_ITEM_TYPE_ATTR = "item_type"
_META = "META"    # item_type 取值：definition item
_STATE = "STATE"  # item_type 取值：运行态 item


def _job_state_to_item(js: JobState) -> dict:
    """JobState → DDB Map entry（字段集同 serialize；session_id=None 用 omit-when-None，读回 .get 得 None）。"""
    d: dict = {"status": js.status.value}
    if js.session_id is not None:
        d["session_id"] = js.session_id
    return d


def _job_state_from_item(scope_id: str, m: dict) -> JobState:
    return JobState(scope_id=scope_id, status=Status(m["status"]), session_id=m.get("session_id"))


def _state_scalars(state: RunState) -> dict:
    """RunState 顶层标量 → DDB 属性（status + omit-when-None 的起止 + hwm，对齐 serialize.run_state_to_dict）。"""
    d: dict = {"status": state.status.value}
    if state.started_at is not None:
        d["started_at"] = state.started_at
    if state.ended_at is not None:
        d["ended_at"] = state.ended_at
    if state.high_water_mark is not None:
        d["high_water_mark"] = state.high_water_mark  # ADR 0034 机制三（数值属性；无状态跑批投影写时有）
    return d


class DynamoDBRunStore:
    """RunStore 的 DynamoDB 实装（组合根注入 boto3 表资源 + 表名）。行为对拍 LocalRunStore。"""

    def __init__(self, table, arg_offloader=None, *, detached: bool = False) -> None:
        """table：boto3 dynamodb.Table 资源（组合根注入；建表责任在 IaC，adapter 假定已存在）。

        arg_offloader：可选 S3StepArgumentOffloader（ADR 0030 决定六）。注入则 RunMeta 深树里的
        docString/dataTable 正文搬 S3、META item 只留指针（解 DDB 400KB 限）；None（默认）则 argument
        原样内联进 meta_json（小 run / 单测省一层 S3）。只挂 RunMeta 写/读路径，RunState 无 argument、不涉及。

        detached（ADR 0034）：本组合根是否「无状态跑批的 submit」——True 则 create_run 的 STATE item 带
        `detached=true` 顶层标记，kicker Lambda 的 Stream filter 只认它（同步 `run --backend cloud` 的
        create_run 无此标记、不触发 kicker——否则双开推进器、重复起 task）。执行环境属性、不进 core 模型。
        """
        require_boto3("DynamoDBRunStore")
        self._table = table
        self._arg_offloader = arg_offloader
        self._detached = detached

    # ---- 实时写三段（ADR 0030 决定六）----

    def create_run(self, meta: RunMeta, initial_state: RunState) -> None:
        """run 开始：写 META（definition，JSON 字符串）+ STATE（初始运行态，jobs 原生 Map）两 item。

        **写序 META→STATE 是契约**（ADR 0034）：kicker 由 STATE 的 INSERT 触发（detached 标记在 STATE 上），
        触发时 META 必已在——若标 META，kicker 可能在 STATE 落库前 tick、claim/投影全 CCF 空转。"""
        meta_dict = run_meta_to_dict(meta)
        if self._arg_offloader is not None:
            # docString/dataTable 正文搬 S3、META 只留指针（解 DDB 400KB 限，ADR 0030 决定六）
            meta_dict = self._arg_offloader.offload(meta_dict, meta.run_id)
        self._table.put_item(Item={
            "run_id": meta.run_id,
            _ITEM_TYPE_ATTR: _META,
            "meta_json": json.dumps(meta_dict, ensure_ascii=False),
        })
        self._table.put_item(Item={
            "run_id": initial_state.run_id,
            _ITEM_TYPE_ATTR: _STATE,
            **({"detached": True} if self._detached else {}),  # kicker filter 只认带此标记的 INSERT（ADR 0034）
            **_state_scalars(initial_state),
            "jobs": {sid: _job_state_to_item(js) for sid, js in initial_state.jobs.items()},
        })

    def update_job_state(self, run_id: str, job_state: JobState) -> None:
        """按 scope_id 单元素刷 STATE.jobs（SET jobs.#sid=:js）。STATE 不存在则报错（须先 create_run）。

        #sid 用 ExpressionAttributeNames 承载任意 scope_id（含 / : 中文，绕开保留字/特殊字符）；
        ConditionExpression 复刻 local「未 create 就报错」——捕 ConditionalCheckFailedException 转 FileNotFoundError。
        """
        try:
            self._table.update_item(
                Key={"run_id": run_id, _ITEM_TYPE_ATTR: _STATE},
                UpdateExpression="SET jobs.#sid = :js",
                ExpressionAttributeNames={"#sid": job_state.scope_id},
                ExpressionAttributeValues={":js": _job_state_to_item(job_state)},
                ConditionExpression="attribute_exists(run_id)",
            )
        except self._table.meta.client.exceptions.ConditionalCheckFailedException as e:
            raise FileNotFoundError(f"update_job_state：STATE 不存在（须先 create_run）：{run_id}") from e

    def finalize_run(self, run_id: str, status: Status, ended_at: str) -> None:
        """commit point：写总 status + ended_at（各 job 态此前已刷）。STATE 不存在则报错。"""
        try:
            self._table.update_item(
                Key={"run_id": run_id, _ITEM_TYPE_ATTR: _STATE},
                UpdateExpression="SET #st = :s, ended_at = :e",
                ExpressionAttributeNames={"#st": "status"},  # status 是 DDB 保留字
                ExpressionAttributeValues={":s": status.value, ":e": ended_at},
                ConditionExpression="attribute_exists(run_id)",
            )
        except self._table.meta.client.exceptions.ConditionalCheckFailedException as e:
            raise FileNotFoundError(f"finalize_run：STATE 不存在（须先 create_run）：{run_id}") from e

    def preflight(self) -> None:
        """探活（ADR 0030 决定七）：begin 前探表可达，表不存在/无权限即抛（cli 接住→退 2）。

        用 `table.load()`（= DescribeTable）——轻量、只读、不写数据；表不存在抛 ResourceNotFoundException、
        无权限抛 AccessDenied，都原样冒泡由组合根 gated except 归到退 2。
        """
        self._table.load()

    # ---- 无状态跑批的条件写三方（ADR 0034）----
    # DDB 原生 ConditionExpression 做原子 CAS——比 local 的 fcntl 文件锁更强（DDB 单 item 写天然原子、
    # 无需外部锁）。真 DDB 条件写行为已真 DDB 实测（moto 与真 DDB 对拍，见 test）。CCF=ConditionalCheckFailedException。

    def try_claim_job(self, run_id: str, scope_id: str) -> bool:
        """CAS：仅当 jobs[scope_id].status == 'pending' 才置 'running'（机制四）。CCF → 已被抢/非 pending → False。"""
        try:
            self._table.update_item(
                Key={"run_id": run_id, _ITEM_TYPE_ATTR: _STATE},
                UpdateExpression="SET jobs.#sid.#st = :running",
                ExpressionAttributeNames={"#sid": scope_id, "#st": "status"},
                ExpressionAttributeValues={":running": Status.RUNNING.value, ":pending": Status.PENDING.value},
                ConditionExpression="jobs.#sid.#st = :pending",  # 仅当前是 pending 才抢占
            )
            return True
        except self._table.meta.client.exceptions.ConditionalCheckFailedException:
            return False

    def project_state(self, run_id: str, state: RunState) -> bool:
        """HWM 条件写 STATE：仅当 (传入 hwm ≥ 库中 hwm) 且 (库中未 finalize) 才写（机制三①）。CCF → stale/已终态 → False。

        **run 级 status 钳为 running/pending、不落终态**（ADR 0030：终态是 finalize 专属；投影提前落终态会挡住
        try_finalize）。条件双守：HWM 挡 stale + status 挡「已 finalize 被刷回」。

        **各 job 态逐 job 单调条件写（机制三②的 job 级半边，对拍 local 的逐 job 合并）**：task_exited 无数值
        seq，两次投影可携带相同 HWM、①挡不住 job 终态被 stale 投影刷回（还会重开 double-launch 窗口，机制四）。
        DDB put_item 表达不了 per-key 条件 → 拆两步：先 update_item 条件写标量（HWM+status 双守，CCF 即整体
        stale 返 False），再对每个 job 用 `SET jobs.#sid=:js` + 「当前非更推进态」的单元素条件写，被挡的单个
        job 静默跳过（库中已更推进，正确态在库、无信息丢失）。两步非原子，但每步各自条件守卫、次序（先标量后
        jobs）保证中间态只会「标量新、job 旧」= 等价于一次携带旧 job 视图的合法投影，下轮重放收敛。
        update_item 天然不碰未提及属性——started_at 由 create_run 落、此处不再传（修「put_item 整 item 覆盖把
        started_at 抹掉」的对拍不一致）。"""
        from core.project import _lifecycle_rank

        new_hwm = state.high_water_mark or 0
        run_status = Status.PENDING.value if state.status == Status.PENDING else Status.RUNNING.value
        try:
            self._table.update_item(
                Key={"run_id": run_id, _ITEM_TYPE_ATTR: _STATE},
                UpdateExpression="SET #st = :s, high_water_mark = :h",
                # (库中无 hwm 或 hwm ≤ 我的) 且 库中 status 仍非终态 → 允许；否则 CCF（stale / 已 finalize）
                ConditionExpression=(
                    "(attribute_not_exists(high_water_mark) OR high_water_mark <= :h) "
                    "AND #st IN (:pending, :running)"
                ),
                ExpressionAttributeNames={"#st": "status"},
                ExpressionAttributeValues={
                    ":s": run_status, ":h": new_hwm,
                    ":pending": Status.PENDING.value, ":running": Status.RUNNING.value,
                },
            )
        except self._table.meta.client.exceptions.ConditionalCheckFailedException:
            return False
        # 机制三② job 级：逐 job 单调条件写。rank 序 pending(0)<running(1)<终态(2)：仅当库中该 job 的 rank
        # 不高于本次投影才写（同 rank 允许覆盖——running 刷 running 幂等、终态间以本次投影为准）。
        for sid, js in state.jobs.items():
            new_rank = _lifecycle_rank(js.status)
            try:
                if new_rank >= 2:
                    # 写终态：库中任何态都可被终态覆盖（终态 rank 最高；job 不存在也允许——补建）
                    cond, vals = None, {}
                elif new_rank == 1:
                    cond, vals = "jobs.#sid.#jst IN (:pending, :running)", {
                        ":pending": Status.PENDING.value, ":running": Status.RUNNING.value}
                else:
                    cond, vals = "jobs.#sid.#jst = :pending", {":pending": Status.PENDING.value}
                kwargs = dict(
                    Key={"run_id": run_id, _ITEM_TYPE_ATTR: _STATE},
                    UpdateExpression="SET jobs.#sid = :js",
                    ExpressionAttributeNames={"#sid": sid, "#jst": "status"} if cond else {"#sid": sid},
                    ExpressionAttributeValues={":js": _job_state_to_item(js), **vals},
                )
                if cond:
                    kwargs["ConditionExpression"] = cond
                self._table.update_item(**kwargs)
            except self._table.meta.client.exceptions.ConditionalCheckFailedException:
                continue  # 库中该 job 已更推进（终态/已 claim）→ 保留库中态，不回退
        return True

    def try_finalize(self, run_id: str, status: Status, ended_at: str) -> bool:
        """状态机单调条件写：仅当总 status ∈ {pending,running} 才写终态（机制三，commit 恰一次）。CCF → 已终态 → False。"""
        try:
            self._table.update_item(
                Key={"run_id": run_id, _ITEM_TYPE_ATTR: _STATE},
                UpdateExpression="SET #st = :s, ended_at = :e",
                ExpressionAttributeNames={"#st": "status"},
                ExpressionAttributeValues={
                    ":s": status.value, ":e": ended_at,
                    ":pending": Status.PENDING.value, ":running": Status.RUNNING.value,
                },
                ConditionExpression="#st IN (:pending, :running)",  # 仅非终态可迁；已终态 → CCF（幂等）
            )
            return True
        except self._table.meta.client.exceptions.ConditionalCheckFailedException:
            return False

    # ---- 一次性写便捷方法（保留，对拍 local）----

    def save_run(self, meta: RunMeta, state: RunState) -> None:
        """一次性写完整态（= create_run 的两 item 一起 put；语义同 local save_run）。"""
        self.create_run(meta, state)

    def load_run_meta(self, run_id: str) -> RunMeta | None:
        """读回 definition（从 META item 的 meta_json）；不存在返回 None。"""
        resp = self._table.get_item(Key={"run_id": run_id, _ITEM_TYPE_ATTR: _META}, ConsistentRead=True)
        item = resp.get("Item")
        if item is None:
            return None
        meta_dict = json.loads(item["meta_json"])
        if self._arg_offloader is not None:
            # content_ref/rows_ref 取回、消解回内联，再交 serialize（对 core 透明，ADR 0030 决定六）
            meta_dict = self._arg_offloader.restore(meta_dict, run_id)
        elif '"content_ref"' in item["meta_json"] or '"rows_ref"' in item["meta_json"]:
            # fail-loud（ADR 0030 决定七「不给生产选要不要正确」）：META 含 offload 指针而本实例没注入
            # offloader = 组合根装配错误（曾发生：Lambda 组合根漏注入 → 正文静默还原成 None、worker 拿
            # 空参数跑错）。宁炸不静默降级。
            raise RuntimeError(
                f"run {run_id} 的 META 含 offload 指针（content_ref/rows_ref）但 RunStore 未注入 "
                "arg_offloader——组合根装配错误（ADR 0030 决定七：offloader 生产默认挂载）")
        return run_meta_from_dict(meta_dict)

    def load_run_state(self, run_id: str) -> RunState | None:
        """读回运行态（从 STATE item，jobs 原生 Map → dict[scope_id, JobState]）；不存在返回 None。

        ConsistentRead=True：commit-point「finalize 后立刻读」的强一致（决定六）。
        """
        resp = self._table.get_item(Key={"run_id": run_id, _ITEM_TYPE_ATTR: _STATE}, ConsistentRead=True)
        item = resp.get("Item")
        if item is None:
            return None
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
            # DDB Number → int（boto3 resource 层给 Decimal）；缺键 → None（同步路径 / 旧数据向后兼容）
            high_water_mark=int(hwm) if hwm is not None else None,
        )
