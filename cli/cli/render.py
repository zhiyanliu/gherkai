"""渲染：把 ADR 0024 事件流与 RunResult 变成人看的文本 / 机器读的 JSON（cli 表层）。

core 产出纯数据（RunResult、Event）；怎么展示是皮的事，故渲染逻辑留在 cli。
"""
from __future__ import annotations

from core.model import Event, RunResult


def format_event(ev: Event) -> str:
    """单个 ADR 0024 事件 → 一行进度文本。"""
    parts: list[str] = [ev.type]
    for attr in ("scope_id", "scenario_id", "step_index", "status"):
        v = getattr(ev, attr, None)
        if v is not None:
            parts.append(f"{attr}={getattr(v, 'value', v)}")
    votes = getattr(ev, "votes", None)
    if votes:
        parts.append(f"votes={votes.yes}/{votes.total}")
    cost = getattr(ev, "cost", None)
    if cost:
        if cost.tokens is not None:
            parts.append(f"tokens={cost.tokens}")
        if cost.time_worked_s is not None:
            parts.append(f"time_worked_s={cost.time_worked_s}")
    return " ".join(str(p) for p in parts)


def _cost_bits(tokens: int | None, time_worked_s: float | None) -> list[str]:
    """原生量成本拼装（core 只合计原生量，美元折算交消费者，ADR 0024）。"""
    bits: list[str] = []
    if tokens is not None:
        bits.append(f"{tokens} tokens")
    if time_worked_s is not None:
        bits.append(f"{time_worked_s:.1f}s agent-time")
    return bits


def _ms(duration_ms: float | None) -> str:
    return f"{duration_ms / 1000:.1f}s" if duration_ms is not None else "?"


def render_text(result: RunResult) -> str:
    """RunResult → 人看的多行汇总（嵌套 job/scenario/step + 时长 + 成本 + 报告指针）。"""
    out: list[str] = ["", "===== RunResult =====", f"  总状态: {result.status.value}"]
    if result.duration_ms is not None:
        out.append(f"  总墙钟时长: {_ms(result.duration_ms)}")
    cost_bits = _cost_bits(result.total_tokens, result.total_time_worked_s)
    if cost_bits:
        out.append(f"  成本原生量合计: {' + '.join(cost_bits)}（美元折算用各自 AWS 账户费率）")

    for jr in result.jobs:
        jbits = _cost_bits(jr.total_tokens, jr.total_time_worked_s)
        cost_str = f"  [{', '.join(jbits)}]" if jbits else ""
        err = f"  ({jr.error_type}: {jr.message})" if jr.error_type else ""
        out.append(f"  job {jr.scope_id!r}: {jr.status.value}{cost_str}{err}")
        if jr.duration_ms is not None:
            out.append(f"    scope 墙钟: {_ms(jr.duration_ms)}")
        for sr in jr.scenarios:
            dur = f"  ({_ms(sr.duration_ms)})" if sr.duration_ms is not None else ""
            out.append(f"    scenario {sr.scenario_id!r}: {sr.status.value}{dur}")
            for st in sr.steps:
                out.append(f"      step[{st.index}]: {st.status.value} ({_ms(st.duration_ms)})")
        if jr.session_id:
            out.append(f"    sessionId: {jr.session_id}")
        for rr in jr.report_refs:
            out.append(f"    report[{rr.granularity}]: {rr.path}")
    return "\n".join(out)


def to_dict(result: RunResult) -> dict:
    """RunResult → 朴素 dict（供 --json；机器可读，CI/WebUI 消费）。

    cost 只含 engine 报的原生量；不折美元（ADR 0024）。
    """
    return {
        "status": result.status.value,
        "duration_ms": result.duration_ms,
        "total_tokens": result.total_tokens,
        "total_time_worked_s": result.total_time_worked_s,
        "jobs": [
            {
                "scope_id": jr.scope_id,
                "status": jr.status.value,
                "duration_ms": jr.duration_ms,
                "total_tokens": jr.total_tokens,
                "total_time_worked_s": jr.total_time_worked_s,
                "session_id": jr.session_id,
                "error_type": jr.error_type,
                "message": jr.message,
                "report_refs": [
                    {"granularity": rr.granularity, "path": rr.path} for rr in jr.report_refs
                ],
                "scenarios": [
                    {
                        "scenario_id": sr.scenario_id,
                        "status": sr.status.value,
                        "duration_ms": sr.duration_ms,
                        "steps": [
                            {
                                "index": st.index,
                                "status": st.status.value,
                                "duration_ms": st.duration_ms,
                                "votes": (
                                    {"yes": st.votes.yes, "total": st.votes.total}
                                    if st.votes
                                    else None
                                ),
                                "error_type": st.error_type,
                            }
                            for st in sr.steps
                        ],
                    }
                    for sr in jr.scenarios
                ],
            }
            for jr in result.jobs
        ],
    }
