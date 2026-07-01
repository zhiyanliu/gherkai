"""渲染：把 ADR 0024 事件流与 RunResult 变成人看的文本 / 机器读的 JSON（cli 表层）。

core 产出纯数据（RunResult、Event）；怎么展示是皮的事，故渲染逻辑留在 cli。
"""
from __future__ import annotations

from core.model import Event, Job, RunResult
from core.serialize import to_dict  # 单一真理源（ADR 0027）：cli --json 与 manifest 共用


def format_event(ev: Event) -> str:
    """单个 ADR 0024 事件 → 一行进度文本（不含 scope_id——scope 归调用方的 `[core <scope>:event]` 前缀，
    见 cli/__main__.py 的 sink；行内只留前缀没有的 scenario_id/step_index/status/votes/cost）。"""
    parts: list[str] = [ev.type]
    for attr in ("scenario_id", "step_index", "status"):
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
    """RunResult → 人看的多行汇总（嵌套 job/scenario/step + 时长 + 成本 + 报告指针）。

    面向人的文本模式：用自然的词、不用变量名式术语（RunResult/sessionId/step[0] 这类）；
    但 job/scenario/step/scope 是领域概念（用户写 feature/看 plan 都在用），保留原词。JSON 模式（to_dict）是
    机器读的、字段名照旧。
    """
    out: list[str] = ["", "===== 运行结果 =====", f"  总状态: {result.status.value}"]
    if result.duration_ms is not None:
        out.append(f"  总墙钟时长: {_ms(result.duration_ms)}")
    cost_bits = _cost_bits(result.total_tokens, result.total_time_worked_s)
    if cost_bits:
        out.append(f"  成本原生量合计: {' + '.join(cost_bits)}")

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
                # 连锁失败旁注（ADR 0031 决定六）：被 scope 内短路的 step（shortcircuited=True，status=skipped）——
                # 上游 error 后 worker 跳过了它、没在损坏环境上跑。旁注解释"为何 skipped"，读 shortcircuited 这个
                # 正交布尔（比旧的"按 status 顺序猜 error 后 failed"精确）；不改判定/severity（守纯 reducer 红线）。
                note = "  ⚠ 因前置 step error 被跳过（未执行）" if st.shortcircuited else ""
                out.append(f"      step {st.index}: {st.status.value} ({_ms(st.duration_ms)}){v}{note}")
                # step 级原生报告产物（Nova trajectory 挂这层，来自 step_done 下沉，ADR 0027）——缩进深一级
                for rr in st.report_refs:
                    out.append(f"        report（{rr.label or rr.kind}）: {rr.ref}")
            # scenario 级原生报告产物：当前引擎均不填（Nova 已下沉 step 级、Midscene 报 scope 级），
            # 保留作扩展兜底——未来引擎若在 scenario_done 报 report_refs 仍能显示（不透明搬运哲学，ADR 0027）
            for rr in sr.report_refs:
                out.append(f"      report（{rr.label or rr.kind}）: {rr.ref}")
        if jr.session_id:
            out.append(f"    session id: {jr.session_id}")
        # scope 级原生报告产物（Midscene report.html 挂这层，来自 scope_done）
        for rr in jr.report_refs:
            out.append(f"    report（{rr.label or rr.kind}）: {rr.ref}")
    return "\n".join(out)


# ---- plan 预检（dry-run）渲染：纯本地、不烧钱，展示 .feature → scope/job 分组 ----

def render_plan_text(jobs: list[Job], default_engine: str) -> str:
    """plan 产出 Job[] → 人看的多行预检视图（scope/engine/scenario/step，不真跑）。"""
    n_scenarios = sum(len(j.scenarios) for j in jobs)
    out: list[str] = [
        "", "===== plan（预检，未真跑）=====",
        f"  {len(jobs)} job(scope)  ·  {n_scenarios} scenario  ·  default_engine={default_engine}",
    ]
    for j in jobs:
        votes = f"  votes={j.assertion_votes}" if j.assertion_votes != 1 else ""
        out.append(f"  job scope={j.scope_id!r} (name={j.scope_name!r}) engine={j.engine}{votes}")
        for sc in j.scenarios:
            out.append(f"    scenario {sc.id!r}  ({len(sc.steps)} step)")
            for st in sc.steps:
                out.append(f"      [{st.index}] {st.keyword} {st.text}{_arg_hint(st.argument)}")
    return "\n".join(out)


def _arg_hint(arg) -> str:
    """step 多行参数的轻量标注（文本视图保持紧凑；完整 content/rows 用 --json 看）。
    dataTable → +dataTable(行×列)；docString → +docString(N 行)。"""
    if arg is None:
        return ""
    if arg.kind == "dataTable":
        rows = arg.rows or ()
        cols = len(rows[0]) if rows else 0
        return f"  +dataTable({len(rows)}×{cols})"
    if arg.kind == "docString":
        n = len((arg.content or "").splitlines())
        return f"  +docString({n} 行)"
    return f"  +{arg.kind}"


def plan_to_dict(jobs: list[Job], default_engine: str) -> dict:
    """plan 产出 → 机器可读 dict（--json）。复用 core.serialize 的 job 序列化保单一真理源。"""
    from core.serialize import job_to_dict
    return {
        "default_engine": default_engine,
        "job_count": len(jobs),
        "scenario_count": sum(len(j.scenarios) for j in jobs),
        "jobs": [job_to_dict(j) for j in jobs],
    }


# to_dict 已移入 core.serialize（单一真理源，cli 与 manifest 共用），从那里 re-export。
__all__ = ["format_event", "render_text", "render_plan_text", "plan_to_dict", "to_dict"]
