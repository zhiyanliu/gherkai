"""wire 协议（ADR 0024）：core↔worker 的 JSON 序列化层 + 退出码约定。

core 把 Job 序列化成 JSON 喂 worker stdin；worker 逐行吐 ADR 0024 事件到专用事件通道（fd，号经
EVENTS_FD 传给 worker；非 stdout——stdout 留给引擎 SDK 噪声，ADR 0024 三通道分离），
core 读行反序列化成 model.Event。这是两端（core 子进程 adapter + 语言无关的 worker）共用的形状约定。

事件行之外，协议还有一条 **out-of-band 通道：worker 退出码**（建连失败早于任何事件 emit，走不了事件
通道，ADR 0024「退出码约定」/ 0028）——故 `EX_WORKER_NETWORK` 与「退出码 → 异常」的翻译也归这里，
各 Engine adapter 只负责把自己传输里的码取出来交给它（见文件末段）。

设计：dataclass ↔ plain dict ↔ JSON。事件按 "type" 字段分派回正确的 Event 子类。
保持手写映射（不靠 dataclasses.asdict 自动），因为 wire 形状是跨语言契约——
worker 可能是 Python 或 Node，两端都按这里的 JSON 形状实现，必须显式、稳定。
"""
from __future__ import annotations

import json

from gherkai_core.errors import WorkerNetworkError
from gherkai_core.model import (
    Cost,
    Event,
    Job,
    ReportRef,
    ResourceUri,
    Scenario,
    ScenarioDone,
    ScenarioStarted,
    ScopeDone,
    ScopeStarted,
    Status,
    Step,
    StepArgument,
    StepDone,
    StepSkipped,
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
        # assertionVotes：AI 断言（Then）投票次数（治种类A抖动，ADR 0014/0024）。worker 据此跑 N 次取多数票。
        # camelCase 与协议其余字段一致；前缀 assertion 点明只作用于 AI 断言（动作 step 无投票）。
        "assertionVotes": job.assertion_votes,
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
    # ref 包成 ResourceUri 仅为命名意图（worker 报的 file://…/s3://… 指针），运行时仍是该字符串。
    return tuple(
        ReportRef(kind=r["kind"], ref=ResourceUri(r["ref"]), label=r.get("label"))
        for r in items
    )


def event_from_json(d: dict) -> Event:
    """JSON dict（worker 事件通道一行）→ model.Event，按 "type" 分派（ADR 0024）。

    事件通道随形态而异：子进程态 = 专用 fd（号经 EVENTS_FD 传给 worker）；Fargate 态 = DDB events 表
    记录的 body（ADR 0024 三通道分离）。两态的行内容同一形状，故都归这里反序列化。
    """
    t = d.get("type")
    if t == "scope_started":
        return ScopeStarted(scope_id=d["scopeId"], session_id=d.get("sessionId"))
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
            report_refs=_report_refs_from_json(d.get("reportRefs")),  # step 级 trajectory（ADR 0027 下沉）
        )
    if t == "step_skipped":
        # scope 内短路（ADR 0031 决定六 / 0024）：独立事件、无 status/votes/cost——加法解析，
        # 不碰上面 step_done 的三态 Status(d["status"]) 分支。core 据此本地赋 StepResult(SKIPPED, shortcircuited=True)。
        return StepSkipped(scenario_id=d["scenarioId"], step_index=d["stepIndex"])
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
    raise ValueError(f"未知事件 type: {t!r}（不符合 worker↔core 协议）")


def event_from_line(line: str) -> Event:
    """worker 事件通道一行（子进程态 = EVENTS_FD 的 fd；Fargate 态 = DDB events 表 body）→ model.Event。"""
    return event_from_json(json.loads(line))


# ============================================================================
# worker → core：退出码（out-of-band 信号，ADR 0024「退出码约定」/ 0028）
# ============================================================================

# worker 网络专用退出码：建连失败、重试耗尽时 worker 以此码退出（建连早于任何事件 emit，无法走事件通道）。
# 值避开 POSIX sysexits(64-78)/shell 保留(126-128+n)/信号区。**两个引擎 worker 各自硬编码同一个值**
# （Nova 的 run_scope.py / Midscene 的 run-scope.ts——语言边界抄不掉）；core 侧只此一处，Engine adapter 一律
# import 本常量与下面的翻译函数，别各抄一份（抄一份 = 两处漂移，靠注释维持一致的人工约束）。
EX_WORKER_NETWORK = 80


def raise_for_worker_exit(rc: int, *, code_label: str) -> None:
    """worker 退出码 → 异常（协议翻译，各 Engine adapter 共用的单一事实源）。

    80 → `WorkerNetworkError`（schedule 记 network_error、可重试整 job，ADR 0028）；其余正非零 →
    `RuntimeError`（worker 异常退出，schedule 记 error）；0 与负码 → 不抛（正常退出 / 被 SIGKILL 强杀，
    后者由调用方各自处置）。

    code_label 只进消息文本：各传输的退出码字段名不同（子进程 `returncode` / ECS `exitCode`），诊断行
    须说该传输的话（也是既有测试匹配的措辞）。
    """
    if rc == EX_WORKER_NETWORK:
        raise WorkerNetworkError(f"worker 建连失败（网络/SSL 瞬时故障），退出码 {rc}")
    if rc > 0:
        raise RuntimeError(f"worker 异常退出 {code_label}={rc}")
