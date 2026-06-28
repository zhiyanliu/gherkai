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

REPO = Path(__file__).resolve().parents[1]
NOVAACT_DIR = REPO / "novaact"
WORKER = NOVAACT_DIR / "worker" / "run_scope.py"


def main() -> int:
    feature_path = Path(sys.argv[1]) if len(sys.argv) > 1 else REPO / "features" / "wikipedia_generic.feature"
    text = feature_path.read_text(encoding="utf-8")
    # uri 用相对仓库根的路径（稳定可读的 id 前缀，ADR 0025）
    uri = str(feature_path.resolve().relative_to(REPO))

    # 1) plan：.feature → Job[]（默认引擎 novaact）
    jobs = plan([FeatureSource(uri=uri, text=text)], PlanConfig(default_engine="novaact"))
    print(f"[e2e] plan: {len(jobs)} job(s)")
    for j in jobs:
        print(f"  - scope={j.scope_id!r} engine={j.engine} scenarios={len(j.scenarios)}")

    # 2) 组合根：子进程 Engine adapter，cmd = novaact 的 venv python 跑 worker，cwd=novaact/
    nova_engine = SubprocessEngine(
        cmd=[str(NOVAACT_DIR / ".venv" / "bin" / "python"), str(WORKER)],
        cwd=str(NOVAACT_DIR),
    )

    def resolver(engine_name: str) -> SubprocessEngine:
        if engine_name == "novaact":
            return nova_engine
        raise ValueError(f"本 e2e 只接了 novaact 腿，不支持 {engine_name!r}")

    # 3) sink：实时打印每个 0024 事件（看进度 + 看 worker 真在吐什么）
    def sink(ev: Event) -> None:
        print(f"  [event] {_fmt_event(ev)}")

    # 4) schedule：单 job 串行（max_concurrency=1，只烧一个会话的钱），给个超时兜底
    print("[e2e] schedule: 起真 Nova Act worker → 真 AgentCore 会话（烧钱）...")
    result = schedule(
        jobs, resolver, sink,
        ScheduleOpts(max_concurrency=1, job_timeout_s=300.0, grace_period_s=10.0),
    )

    # 5) 汇总
    print(f"\n[e2e] ===== RunResult =====")
    print(f"  总状态: {result.status.value}")
    for jr in result.jobs:
        print(f"  job {jr.scope_id!r}: {jr.status.value}"
              + (f"  ({jr.error_type}: {jr.message})" if jr.error_type else ""))
        for sr in jr.scenarios:
            print(f"    scenario {sr.scenario_id!r}: {sr.status.value}")
        if jr.session_id:
            print(f"    sessionId: {jr.session_id}")
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
        parts.append(f"cost_usd={cost.cost_usd}")
    return " ".join(str(p) for p in parts)


if __name__ == "__main__":
    sys.exit(main())
