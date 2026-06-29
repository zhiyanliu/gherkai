"""wire 协议（ADR 0024）：core↔worker 的 JSON 序列化层。

core 把 Job 序列化成 JSON 喂 worker stdin；worker 逐行吐 ADR 0024 事件到专用事件通道（fd，号经
EVENTS_FD 传给 worker；非 stdout——stdout 留给引擎 SDK 噪声，ADR 0024 三通道分离），
core 读行反序列化成 model.Event。这是两端（core 子进程 adapter + 语言无关的 worker）共用的形状约定。

设计：dataclass ↔ plain dict ↔ JSON。事件按 "type" 字段分派回正确的 Event 子类。
保持手写映射（不靠 dataclasses.asdict 自动），因为 wire 形状是跨语言契约——
worker 可能是 Python 或 Node，两端都按这里的 JSON 形状实现，必须显式、稳定。
"""
from __future__ import annotations

import json

from core.model import (
    Cost,
    Event,
    Job,
    ReportRef,
    Scenario,
    ScenarioDone,
    ScenarioStarted,
    ScopeDone,
    ScopeStarted,
    Status,
    Step,
    StepArgument,
    StepDone,
    StepStarted,
    Votes,
)


# ============================================================================
# core → worker：Job 序列化
# ============================================================================


def _argument_to_json(arg: StepArgument | None) -> dict | None:
    if arg is None:
        return None
    if arg.kind == "docString":
        return {"kind": "docString", "content": arg.content}
    return {"kind": "dataTable", "rows": [list(r) for r in (arg.rows or ())]}


def _step_to_json(step: Step) -> dict:
    d: dict = {"index": step.index, "keyword": step.keyword, "text": step.text}
    arg = _argument_to_json(step.argument)
    if arg is not None:
        d["argument"] = arg
    return d


def _scenario_to_json(sc: Scenario) -> dict:
    return {
        "id": sc.id,
        "name": sc.name,
        "steps": [_step_to_json(s) for s in sc.steps],
    }


def job_to_json(job: Job) -> dict:
    """Job → JSON dict（喂 worker stdin，ADR 0024 输入形状）。"""
    return {
        "scope": {"id": job.scope_id, "name": job.scope_name},
        "engine": job.engine,
        "scenarios": [_scenario_to_json(sc) for sc in job.scenarios],
    }


def job_to_line(job: Job) -> str:
    """Job → 单行 JSON 字符串（写 worker stdin）。"""
    return json.dumps(job_to_json(job), ensure_ascii=False)


# ============================================================================
# worker → core：Event 反序列化
# ============================================================================


def _cost_from_json(d: dict | None) -> Cost | None:
    if d is None:
        return None
    # 只认 engine 报的原生量（平铺、各 optional，ADR 0024）：tokens / time_worked_s，无折算美元
    return Cost(
        tokens=d.get("tokens"),
        time_worked_s=d.get("time_worked_s"),
    )


def _votes_from_json(d: dict | None) -> Votes | None:
    if d is None:
        return None
    return Votes(yes=d["yes"], total=d["total"])


def _report_refs_from_json(items: list | None) -> tuple[ReportRef, ...]:
    if not items:
        return ()
    # 不透明搬运（ADR 0027）：原样读 kind/ref/label，不校验 kind 值、不解释 ref。
    return tuple(
        ReportRef(kind=r["kind"], ref=r["ref"], label=r.get("label"))
        for r in items
    )


def event_from_json(d: dict) -> Event:
    """JSON dict（worker stdout 一行）→ model.Event，按 "type" 分派（ADR 0024）。"""
    t = d.get("type")
    if t == "scope_started":
        return ScopeStarted(scope_id=d["scopeId"])
    if t == "scenario_started":
        return ScenarioStarted(scenario_id=d["scenarioId"])
    if t == "step_started":
        return StepStarted(scenario_id=d["scenarioId"], step_index=d["stepIndex"])
    if t == "step_done":
        return StepDone(
            scenario_id=d["scenarioId"],
            step_index=d["stepIndex"],
            status=Status(d["status"]),
            votes=_votes_from_json(d.get("votes")),
            cost=_cost_from_json(d.get("cost")),
            error_type=d.get("errorType"),
            message=d.get("message"),
        )
    if t == "scenario_done":
        return ScenarioDone(
            scenario_id=d["scenarioId"],
            status=Status(d["status"]),
            report_refs=_report_refs_from_json(d.get("reportRefs")),
        )
    if t == "scope_done":
        return ScopeDone(
            scope_id=d["scopeId"],
            session_id=d.get("sessionId"),
            report_refs=_report_refs_from_json(d.get("reportRefs")),
        )
    raise ValueError(f"未知事件 type: {t!r}（不符合 ADR 0024 协议）")


def event_from_line(line: str) -> Event:
    """worker stdout 一行 → model.Event。"""
    return event_from_json(json.loads(line))
