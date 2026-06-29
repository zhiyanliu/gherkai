"""渲染：把 ADR 0024 事件流与 RunResult 变成人看的文本 / 机器读的 JSON（cli 表层）。

core 产出纯数据（RunResult、Event）；怎么展示是皮的事，故渲染逻辑留在 cli。
"""
from __future__ import annotations

from core.model import Event, RunResult
from core.serialize import to_dict  # 单一真理源（ADR 0027）：cli --json 与 manifest 共用


def format_event(ev: Event) -> str:
    """单个 ADR 0024 事件 → 一行进度文本。"""
    parts: list[str] = [ev.type]
    for attr in ("scope_id", "scenario_id", "step_index", "status"):
        v = getattr(ev, attr, None)
        if v is not None:
            parts.append(f"{attr}={getattr(v, 'value', v)}")
    votes = getattr(ev, "votes", None)
    if votes and votes.total > 1:  # total==1=单次判定，无抖动 tally 意义，不显（避免 1/1 噪声）
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
                # total>1 才显投票 tally（与 format_event/index.html 一致；1/1 无抖动意义，不显）
                v = f" 投票 {st.votes.yes}/{st.votes.total}" if st.votes and st.votes.total > 1 else ""
                out.append(f"      step[{st.index}]: {st.status.value} ({_ms(st.duration_ms)}){v}")
        if jr.session_id:
            out.append(f"    sessionId: {jr.session_id}")
        for rr in jr.report_refs:
            out.append(f"    report[{rr.kind}]: {rr.ref}")
    return "\n".join(out)


# to_dict 已移入 core.serialize（单一真理源，cli 与 manifest 共用），从那里 re-export。
__all__ = ["format_event", "render_text", "to_dict"]
