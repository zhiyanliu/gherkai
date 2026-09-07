"""子进程 Engine adapter 集成测试（ADR 0026 机制层）。

用 tests/fixtures/echo_worker.py 当真子进程 spawn，验证 spawn/stdin/stdout/SIGTERM 整条管道
+ 与 schedule 配合，全程不接真引擎、不烧 AWS。
"""
from __future__ import annotations

import sys
import time
from pathlib import Path

from gherkai_core.adapters.subprocess_engine import SubprocessEngine
from gherkai_core.model import Job, RunMeta, Scenario, ScopeDone, ScopeStarted, Status, Step
from gherkai_core.schedule import schedule, ScheduleOpts
from tests.fake_engine import CollectSink

_WORKER = str(Path(__file__).parent / "fixtures" / "echo_worker.py")


def _rm(jobs: list[Job], run_id: str = "test-run") -> RunMeta:
    return RunMeta(run_id=run_id, created_at="", jobs=tuple(jobs))


def _engine(mode: str) -> SubprocessEngine:
    import os
    env = {**os.environ, "WORKER_MODE": mode}
    return SubprocessEngine(cmd=[sys.executable, _WORKER], env=env)


def _job(scope_id: str = "s", timeout_s: float | None = None) -> Job:
    return Job(
        scope_id=scope_id, scope_name=scope_id, engine="novaact", timeout_s=timeout_s,
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
    evs = list(events)  # 消费整个流（adapter 是纯 Event，无心跳——心跳在 schedule 层）
    types = [e.type for e in evs]
    assert types == ["scope_started", "scenario_started", "step_done", "step_done", "step_done", "scenario_done", "scope_done"]
    # Then step 带 votes
    then_ev = [e for e in evs if e.type == "step_done"][2]
    assert then_ev.votes is not None and then_ev.votes.yes == 3
    # scope_started 与 scope_done 都带 sessionId（ADR 0028：血缘随首事件即回传，scope_done 冗余兜底）
    assert isinstance(evs[0], ScopeStarted)
    assert evs[0].session_id == "echo-sess"
    scope_done = evs[-1]
    assert isinstance(scope_done, ScopeDone)
    assert scope_done.session_id == "echo-sess"


# ---- adapter + schedule 端到端（跨进程，假 worker）----
def test_adapter_with_schedule_pass():
    engine = _engine("pass")
    result = schedule(_rm([_job("s")]), lambda name: engine, CollectSink())
    assert result.status == Status.PASSED
    assert result.jobs[0].status == Status.PASSED
    assert result.jobs[0].session_id == "echo-sess"


# ---- worker 崩（非零退出）→ schedule 记 error ----
def test_adapter_crash_is_error():
    engine = _engine("crash")
    result = schedule(_rm([_job("s")]), lambda name: engine, CollectSink())
    assert result.status == Status.ERROR
    assert result.jobs[0].status == Status.ERROR
    assert result.jobs[0].error_type == "engine_error"


# ---- worker 以 EX_WORKER_NETWORK(80) 退出 → adapter 翻 WorkerNetworkError → schedule 记 network_error ----
# 这是退出码→分类链路唯一的真跨进程 seam（ADR 0028），FakeEngine 直接 raise 绕不过它，必须真 spawn。
def test_adapter_network_exit_maps_to_network_error():
    from gherkai_core.errors import WorkerNetworkError
    engine = _engine("net")
    # 直接用 adapter：消费事件流应抛 WorkerNetworkError（returncode 80 翻译）
    handle, events = engine.run_scope(_job("s"))
    raised = None
    try:
        list(events)
    except WorkerNetworkError as e:
        raised = e
    assert raised is not None, "exit 80 应被 adapter 翻成 WorkerNetworkError"


def test_adapter_network_error_with_schedule_classified_and_retried():
    from gherkai_core.schedule import ScheduleOpts
    engine = _engine("net")
    # 经 schedule：记 network_error；开 network_retry=1 → 真重新 spawn worker（净跨进程验证）
    result = schedule(_rm([_job("s")]), lambda name: engine, CollectSink(),
                      opts=ScheduleOpts(network_retry=1, retry_sleep=lambda _s: None))
    assert result.status == Status.ERROR
    assert result.jobs[0].error_type == "network_error"  # exit 80 → 真 seam → network_error


# ---- worker 卡死 → SIGTERM 停止（adapter handle.stop 直接测）----
def test_adapter_stop_hanging_worker():
    engine = _engine("hang")
    handle, events = engine.run_scope(_job("s"))
    # 先拿到第一个事件（worker 已起、进入死循环）。adapter 是纯 Event 流，无心跳。
    it = iter(events)
    first = next(it)
    assert first.type == "scope_started"  # 首事件现在是 scope_started（带 sessionId，ADR 0028）
    # stop：SIGTERM → worker 的 finally 清理 → 退出（宽限足够）
    t0 = time.monotonic()
    handle.stop(grace_period_s=5.0)
    elapsed = time.monotonic() - t0
    assert elapsed < 5.0  # worker 响应 SIGTERM 优雅退出，没等到宽限超时强杀


# ---- worker 无视 SIGTERM → adapter grace 超时 → SIGKILL 兜底（terminate→wait 超时→proc.kill 分支）----
def test_adapter_sigkill_backstop_on_deaf_worker():
    # deaf worker 装 SIG_IGN 忽略 SIGTERM、死循环不退——逼 SubprocessWorkerHandle.stop 走
    # TimeoutExpired→proc.kill() 兜底（其余 mode 都优雅退、不踩这条尾路径，本测试专补它）。
    engine = _engine("deaf")
    handle, events = engine.run_scope(_job("s"))
    it = iter(events)
    assert next(it).type == "scope_started"  # worker 已起、进入忽略信号的死循环
    # stop：SIGTERM 被忽略 → 等满 grace → SIGKILL 强杀。用短 grace 让测试快。
    t0 = time.monotonic()
    handle.stop(grace_period_s=0.5)
    elapsed = time.monotonic() - t0
    assert elapsed >= 0.5  # 确实等满了 grace（SIGTERM 没生效、走到超时）
    assert elapsed < 3.0   # 但 SIGKILL 后随即返回、不会永远挂着
    # 进程确被强杀：adapter 的 proc.kill() 是异步 SIGKILL、不 wait，故给 OS 一点回收时间再确认终止。
    proc = handle._proc  # type: ignore[attr-defined]
    assert proc.wait(timeout=3.0) is not None  # 已终止（SIGKILL 下 returncode 为负 signal，非 None）
    assert proc.returncode != 0  # 被信号杀（非协作退 0）——SIGKILL 惯例 -9


# ---- #1（ADR 0028）：worker 静默卡死（吐 started 后不再吐事件）→ schedule 的 _heartbeat_wrap 让 job_timeout 能触发 ----
# 真跨进程验证：silent worker 卡在死循环、fd3 零新事件。adapter 的事件流是纯阻塞读，靠 schedule 层
# _heartbeat_wrap（后台线程 + queue 超时）周期性醒来查 deadline——否则超时永不触发（曾致 300s 拖到 ~620s）。
def test_silent_worker_timeout_fires_via_heartbeat():
    engine = _engine("silent")
    t0 = time.monotonic()
    # job_timeout=1s：silent worker 吐完 scope_started/scenario_started 即静默；靠心跳，schedule 应在
    # ~1s（+ 一个心跳间隔 + grace）内超时杀掉，而非永久挂起。给宽松上限 15s 兜底（仍远小于"永不触发"）。
    result = schedule(
        _rm([_job("s", timeout_s=1.0)]), lambda name: engine, CollectSink(),
        opts=ScheduleOpts(grace_period_s=5.0, heartbeat_interval_s=0.2),
    )
    elapsed = time.monotonic() - t0
    assert result.jobs[0].status == Status.ERROR
    assert result.jobs[0].error_type == "timeout"  # 超时分类（非 engine_error）
    assert elapsed < 15.0, f"超时应靠心跳准时触发，实际耗时 {elapsed:.1f}s（疑似退回阻塞死等）"


# ---- #2（ADR 0028）：session_id 经 scope_started 提前回传 → 超时/中止 scope_done 缺席时仍记得到血缘 ----
def test_session_id_captured_from_scope_started_on_timeout():
    engine = _engine("silent")
    result = schedule(
        _rm([_job("s", timeout_s=1.0)]), lambda name: engine, CollectSink(),
        opts=ScheduleOpts(grace_period_s=5.0),
    )
    # silent worker 超时被杀、从未 emit scope_done——但 session_id 已随 scope_started 落到 result（ADR 0028）
    assert result.jobs[0].status == Status.ERROR
    assert result.jobs[0].session_id == "echo-sess", "超时路径下 session_id 应仍从 scope_started 捕获到"


# ---- #2 直接验证：scope_started 事件本身带 sessionId（协议层，不经超时）----
def test_scope_started_carries_session_id():
    engine = _engine("silent")
    handle, events = engine.run_scope(_job("s"))
    first = next(iter(events))  # adapter 事件流是纯 Event（心跳在 schedule 层，不在此）
    assert isinstance(first, ScopeStarted)
    assert first.session_id == "echo-sess"
    handle.stop(grace_period_s=5.0)  # 收尾杀掉 silent worker
