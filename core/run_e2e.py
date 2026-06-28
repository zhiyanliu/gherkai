"""端到端撞真引擎（ADR 0024/0026 第一次真跑）：组合根接线 + 烧真 AWS 钱。

core plan(.feature) → schedule(注入子进程 Engine adapter) → 真 Nova Act worker
→ 真 AgentCore 会话 → 回 0024 事件 → RunResult。

这是 CLI 的雏形 = 组合根：在这里 new 出具体 adapter（子进程 Engine，cmd 指向 Nova worker）注入给 core。
core 本身不知道 worker 是子进程、不知道是 Nova Act。

跑：cd core && uv run python run_e2e.py [feature路径]
默认跑 ../features/wikipedia_generic.feature。需 AWS 凭证 + region us-east-1（烧钱！）。
"""
from __future__ import annotations

import sys
from pathlib import Path

from core.adapters.subprocess_engine import SubprocessEngine
from core.model import Event
from core.scope import FeatureSource, PlanConfig, plan
from core.schedule import ScheduleOpts, schedule

import os

REPO = Path(__file__).resolve().parents[1]
NOVAACT_DIR = REPO / "novaact"
MIDSCENE_DIR = REPO / "midscene"


def main() -> int:
    feature_path = Path(sys.argv[1]) if len(sys.argv) > 1 else REPO / "features" / "wikipedia_generic.feature"
    text = feature_path.read_text(encoding="utf-8")
    # uri 用相对仓库根的路径（稳定可读的 id 前缀，ADR 0025）
    uri = str(feature_path.resolve().relative_to(REPO))

    default_engine = os.environ.get("DEFAULT_ENGINE", "novaact")

    # 1) plan：.feature → Job[]
    jobs = plan([FeatureSource(uri=uri, text=text)], PlanConfig(default_engine=default_engine))
    print(f"[e2e] plan: {len(jobs)} job(s)  (default_engine={default_engine})")
    for j in jobs:
        print(f"  - scope={j.scope_id!r} engine={j.engine} scenarios={len(j.scenarios)}")

    # 2) 组合根：每条腿一个子进程 Engine adapter（cmd 不同、core 引擎无关，ADR 0026）
    #    Nova Act 腿：novaact venv 的 python 跑 worker
    nova_engine = SubprocessEngine(
        cmd=[str(NOVAACT_DIR / ".venv" / "bin" / "python"), str(NOVAACT_DIR / "worker" / "run_scope.py")],
        cwd=str(NOVAACT_DIR),
    )
    #    Midscene 腿：node --import tsx 跑 TS worker。
    #    用 `--import tsx`（不是 tsx 二进制、也不是 `tsx/esm`）：tsx loader 加载进**同一个** node 进程，
    #    不 spawn 子-node——否则 EVENTS_FD（经 pass_fds 继承）只到 tsx 包装器、传不到真正跑 worker 的子进程
    #    → fd3 EBADF（实测踩过）。`--import tsx` 既继承 fd、又能跑 .ts，不触发 ESM require cycle。
    midscene_engine = SubprocessEngine(
        cmd=["node", "--import", "tsx", str(MIDSCENE_DIR / "worker" / "run-scope.ts")],
        cwd=str(MIDSCENE_DIR),
    )

    def resolver(engine_name: str) -> SubprocessEngine:
        if engine_name == "novaact":
            return nova_engine
        if engine_name == "midscene":
            return midscene_engine
        raise ValueError(f"未知引擎 {engine_name!r}（支持 novaact / midscene）")

    # 3) sink：实时打印每个 0024 事件（看进度 + 看 worker 真在吐什么）
    def sink(ev: Event) -> None:
        print(f"  [event] {_fmt_event(ev)}")

    # 4) schedule：并发上限可配（env MAX_CONCURRENCY，默认 1），给个超时兜底
    max_conc = int(os.environ.get("MAX_CONCURRENCY", "1"))
    job_timeout = float(os.environ.get("JOB_TIMEOUT", "300"))
    print(f"[e2e] schedule: 起真 Nova Act worker → 真 AgentCore 会话（烧钱）"
          f"max_concurrency={max_conc} job_timeout={job_timeout}s...")
    result = schedule(
        jobs, resolver, sink,
        ScheduleOpts(max_concurrency=max_conc, job_timeout_s=job_timeout, grace_period_s=10.0),
    )

    # 5) 汇总（成本：core 只合计 engine 原生量，美元折算交消费者，ADR 0024）
    print(f"\n[e2e] ===== RunResult =====")
    print(f"  总状态: {result.status.value}")
    if result.duration_ms is not None:
        print(f"  总墙钟时长: {result.duration_ms/1000:.1f}s")
    cost_bits = []
    if result.total_tokens is not None:
        cost_bits.append(f"{result.total_tokens} tokens")
    if result.total_time_worked_s is not None:
        cost_bits.append(f"{result.total_time_worked_s:.1f}s agent-time")
    if cost_bits:
        print(f"  成本原生量合计: {' + '.join(cost_bits)}（美元折算用各自 AWS 账户费率）")
    for jr in result.jobs:
        bits = []
        if jr.total_tokens is not None:
            bits.append(f"{jr.total_tokens} tokens")
        if jr.total_time_worked_s is not None:
            bits.append(f"{jr.total_time_worked_s:.1f}s")
        cost_str = f"  [{', '.join(bits)}]" if bits else ""
        print(f"  job {jr.scope_id!r}: {jr.status.value}{cost_str}"
              + (f"  ({jr.error_type}: {jr.message})" if jr.error_type else ""))
        if jr.duration_ms is not None:
            print(f"    scope 墙钟: {jr.duration_ms/1000:.1f}s")
        for sr in jr.scenarios:
            dur = f"  ({sr.duration_ms/1000:.1f}s)" if sr.duration_ms is not None else ""
            print(f"    scenario {sr.scenario_id!r}: {sr.status.value}{dur}")
            for st in sr.steps:
                sd = f"{st.duration_ms/1000:.1f}s" if st.duration_ms is not None else "?"
                print(f"      step[{st.index}]: {st.status.value} ({sd})")
        if jr.session_id:
            print(f"    sessionId: {jr.session_id}")
        for rr in jr.report_refs:
            print(f"    report[{rr.granularity}]: {rr.path}")
    return 0 if result.status.value == "passed" else 1


def _fmt_event(ev: Event) -> str:
    parts = [ev.type]
    for attr in ("scenario_id", "scope_id", "step_index", "status"):
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


if __name__ == "__main__":
    sys.exit(main())
