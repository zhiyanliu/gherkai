"""DynamoDBRunStore（ADR 0030 决定六）：RunStore port 的 DynamoDB 实装。

对拍 `LocalRunStore` 的行为（同一批 round-trip/生命周期/报错语义），只换落点为 DDB。**云端 adapter，需 boto3**
（`core[aws]` optional extra，缺它 import 本模块不崩、构造时才友好报错，守 [0016] 窄腰）。

表 schema（决定六）：`PK=run_id`，`SK='META' | 'STATE'`——RunMeta 与 RunState **分两 item**：
- **META item**：`{run_id, sk='META', meta_json=<json.dumps(run_meta_to_dict)>}`。RunMeta 是 definition，
  **write-once（create_run）/ read-whole（load_run_meta）**，从不单元素更新——故整体存 JSON 字符串最简、
  且躲开 DDB 原生 Map 对空串/嵌套 list 的挑剔（DataTable rows 常含空 cell）。第 4 步 offload 在 `json.dumps`
  **前**对 dict 里的 docString/dataTable 换指针，不需要 META 是原生 Map。
- **STATE item**：`{run_id, sk='STATE', status, started_at?, ended_at?, jobs=<原生 Map>}`。jobs **必须原生 Map**
  才能 `SET jobs.#sid=:js` 按 scope_id 单元素刷（决定六）；其 entry 全是 str（无 float），原生 Map 无 Decimal 顾虑。

字段仍源于 `serialize`（单一真理源）：META 直接 `json.dumps(run_meta_to_dict)`；STATE 的标量 + jobs 各 entry
的字段集取自 `run_state_to_dict`，只是 jobs 的**容器形状**在本 adapter 从 list 特化成 Map（非第二真理源）。

建表责任在 IaC/组合根、非本 adapter——adapter 假定表已存在（决定六；测试由 conftest fixture 建表）。
"""
from __future__ import annotations

import json

from core.model import JobState, RunMeta, RunState, Status
from core.serialize import (
    run_meta_from_dict,
    run_meta_to_dict,
)

_META_SK = "META"
_STATE_SK = "STATE"


def _require_boto3():
    """云端 adapter 缺 boto3 时给友好提示（模块 import 不崩、构造时才检；守 [0016] 窄腰、方案 A）。"""
    try:
        import botocore.exceptions  # noqa: F401
    except ImportError as e:  # pragma: no cover
        raise ImportError(
            "DynamoDBRunStore 需要 boto3——请装云端依赖：`pip install core[aws]`（或 uv 装 aws extra）"
        ) from e


def _job_state_to_item(js: JobState) -> dict:
    """JobState → DDB Map entry（字段集同 serialize；session_id=None 用 omit-when-None，读回 .get 得 None）。"""
    d: dict = {"status": js.status.value}
    if js.session_id is not None:
        d["session_id"] = js.session_id
    return d


def _job_state_from_item(scope_id: str, m: dict) -> JobState:
    return JobState(scope_id=scope_id, status=Status(m["status"]), session_id=m.get("session_id"))


def _state_scalars(state: RunState) -> dict:
    """RunState 顶层标量 → DDB 属性（status + omit-when-None 的起止，对齐 serialize.run_state_to_dict）。"""
    d: dict = {"status": state.status.value}
    if state.started_at is not None:
        d["started_at"] = state.started_at
    if state.ended_at is not None:
        d["ended_at"] = state.ended_at
    return d


class DynamoDBRunStore:
    """RunStore 的 DynamoDB 实装（组合根注入 boto3 表资源 + 表名）。行为对拍 LocalRunStore。"""

    def __init__(self, table) -> None:
        """table：boto3 dynamodb.Table 资源（组合根注入；建表责任在 IaC，adapter 假定已存在）。"""
        _require_boto3()
        self._table = table

    # ---- 实时写三段（ADR 0030 决定六）----

    def create_run(self, meta: RunMeta, initial_state: RunState) -> None:
        """run 开始：写 META（definition，JSON 字符串）+ STATE（初始运行态，jobs 原生 Map）两 item。"""
        self._table.put_item(Item={
            "run_id": meta.run_id,
            "sk": _META_SK,
            "meta_json": json.dumps(run_meta_to_dict(meta), ensure_ascii=False),
        })
        self._table.put_item(Item={
            "run_id": initial_state.run_id,
            "sk": _STATE_SK,
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
                Key={"run_id": run_id, "sk": _STATE_SK},
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
                Key={"run_id": run_id, "sk": _STATE_SK},
                UpdateExpression="SET #st = :s, ended_at = :e",
                ExpressionAttributeNames={"#st": "status"},  # status 是 DDB 保留字
                ExpressionAttributeValues={":s": status.value, ":e": ended_at},
                ConditionExpression="attribute_exists(run_id)",
            )
        except self._table.meta.client.exceptions.ConditionalCheckFailedException as e:
            raise FileNotFoundError(f"finalize_run：STATE 不存在（须先 create_run）：{run_id}") from e

    # ---- 一次性写便捷方法（保留，对拍 local）----

    def save_run(self, meta: RunMeta, state: RunState) -> None:
        """一次性写完整态（= create_run 的两 item 一起 put；语义同 local save_run）。"""
        self.create_run(meta, state)

    def load_run_meta(self, run_id: str) -> RunMeta | None:
        """读回 definition（从 META item 的 meta_json）；不存在返回 None。"""
        resp = self._table.get_item(Key={"run_id": run_id, "sk": _META_SK}, ConsistentRead=True)
        item = resp.get("Item")
        if item is None:
            return None
        return run_meta_from_dict(json.loads(item["meta_json"]))

    def load_run_state(self, run_id: str) -> RunState | None:
        """读回运行态（从 STATE item，jobs 原生 Map → dict[scope_id, JobState]）；不存在返回 None。

        ConsistentRead=True：commit-point「finalize 后立刻读」的强一致（决定六）。
        """
        resp = self._table.get_item(Key={"run_id": run_id, "sk": _STATE_SK}, ConsistentRead=True)
        item = resp.get("Item")
        if item is None:
            return None
        jobs = {
            sid: _job_state_from_item(sid, m)
            for sid, m in (item.get("jobs") or {}).items()
        }
        return RunState(
            run_id=item["run_id"],
            status=Status(item["status"]),
            jobs=jobs,
            started_at=item.get("started_at"),
            ended_at=item.get("ended_at"),
        )
