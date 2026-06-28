"""子进程 Engine adapter 集成测试（ADR 0026 机制层）。

用 tests/fixtures/echo_worker.py 当真子进程 spawn，验证 spawn/stdin/stdout/SIGTERM 整条管道
+ 与 schedule 配合，全程不接真引擎、不烧 AWS。
"""
from __future__ import annotations

import sys
import time
from pathlib import Path

from core.adapters.subprocess_engine import SubprocessEngine
from core.model import Job, Scenario, ScopeDone, Status, Step
from core.schedule import schedule
from tests.fake_engine import CollectSink

_WORKER = str(Path(__file__).parent / "fixtures" / "echo_worker.py")


def _engine(mode: str) -> SubprocessEngine:
    import os
    env = {**os.environ, "WORKER_MODE": mode}
    return SubprocessEngine(cmd=[sys.executable, _WORKER], env=env)


def _job(scope_id: str = "s") -> Job:
    return Job(
        scope_id=scope_id, scope_name=scope_id, engine="novaact",
        scenarios=(
            Scenario(id=f"{scope_id}:0", name="sc", steps=(
                Step(0, "Given", '打开 "https://x"'),
                Step(1, "When", "搜索"),
                Step(2, "Then", "进入页面"),
            )),
        ),
    )


# ---- 直接用 adapter：spawn → 喂 job → 读回事件 ----
def test_adapter_roundtrip_pass():
    engine = _engine("pass")
    handle, events = engine.run_scope(_job("s"))
    evs = list(events)  # 消费整个流
    types = [e.type for e in evs]
    assert types == ["scenario_started", "step_done", "step_done", "step_done", "scenario_done", "scope_done"]
    # Then step 带 votes
    then_ev = [e for e in evs if e.type == "step_done"][2]
    assert then_ev.votes is not None and then_ev.votes.yes == 3
    # scope_done 带 sessionId
    scope_done = evs[-1]
    assert isinstance(scope_done, ScopeDone)
    assert scope_done.session_id == "echo-sess"


# ---- adapter + schedule 端到端（跨进程，假 worker）----
def test_adapter_with_schedule_pass():
    engine = _engine("pass")
    result = schedule([_job("s")], lambda name: engine, CollectSink())
    assert result.status == Status.PASSED
    assert result.jobs[0].status == Status.PASSED
    assert result.jobs[0].session_id == "echo-sess"


# ---- worker 崩（非零退出）→ schedule 记 error ----
def test_adapter_crash_is_error():
    engine = _engine("crash")
    result = schedule([_job("s")], lambda name: engine, CollectSink())
    assert result.status == Status.ERROR
    assert result.jobs[0].status == Status.ERROR
    assert result.jobs[0].error_type == "engine_error"


# ---- worker 卡死 → SIGTERM 停止（adapter handle.stop 直接测）----
def test_adapter_stop_hanging_worker():
    engine = _engine("hang")
    handle, events = engine.run_scope(_job("s"))
    # 先拿到第一个事件（worker 已起、进入死循环）
    it = iter(events)
    first = next(it)
    assert first.type == "scenario_started"
    # stop：SIGTERM → worker 的 finally 清理 → 退出（宽限足够）
    t0 = time.monotonic()
    handle.stop(grace_period_s=5.0)
    elapsed = time.monotonic() - t0
    assert elapsed < 5.0  # worker 响应 SIGTERM 优雅退出，没等到宽限超时强杀
