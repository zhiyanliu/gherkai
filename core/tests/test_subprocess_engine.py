"""子进程 Engine adapter 集成测试（ADR 0026 机制层）。

用 tests/fixtures/echo_worker.py 当真子进程 spawn，验证 spawn/stdin/stdout/SIGTERM 整条管道
+ 与 schedule 配合，全程不接真引擎、不产生 AWS 费用。
"""
from __future__ import annotations

import sys
import time
from pathlib import Path

from gherkai_core.adapters.subprocess_engine import SubprocessEngine
from gherkai_core.model import Job, RunMeta, Scenario, ScopeDone, ScopeStarted, Status, Step, StepArgument
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
                Step(0, "Given", '"https://x"'),
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
    assert proc.returncode != 0  # 被信号杀（非协作以退出码 0 退出）——SIGKILL 惯例 -9


# ---- ADR 0028「静默 worker 超时根治」条：worker 静默卡死（吐 started 后不再吐事件）→ schedule 的 _heartbeat_wrap 让 job_timeout 能触发 ----
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


# ---- 停止与收尾的真子进程护栏（ADR 0034 机制二：首次仲裁、内容完整后不再仲裁、停止后有界消费）----


def _mode_job(scope_id: str, mode: str, timeout_s: float | None = None) -> Job:
    j = _job(scope_id, timeout_s=timeout_s)
    return Job(scope_id=j.scope_id, scope_name=f"mode:{mode}", engine=j.engine, scenarios=j.scenarios, timeout_s=timeout_s)


def test_fail_fast_stops_multiple_deaf_victims_in_parallel(tmp_path):
    """fail-fast 对多个仍在运行的真子进程：先全部落定再并行发停止请求。关掉心跳，victim 的线程阻塞在管道读上、看不到 abort_flag，
    只有主线程的 _stop_all 能停它们；victim 无视 SIGTERM（各自要等满宽限才被 SIGKILL），并行停的总耗时约等于一份宽限、串行停至少两份
    ——耗时上界把并行钉死；crash job 等两个 victim 都已装好 SIG_IGN 并发出 scope_started 才崩。两个 victim 都判 ABORTED。"""
    import os
    import threading

    gate = tmp_path / "crash-now"
    engine = SubprocessEngine(cmd=[sys.executable, _WORKER], env={**os.environ, "WORKER_MODE": "pass", "WORKER_CRASH_AFTER_FILE": str(gate)})
    ready: set[str] = set()
    lock = threading.Lock()

    class _Sink(CollectSink):
        def __call__(self, ev):
            super().__call__(ev)
            if isinstance(ev, ScopeStarted) and ev.scope_id in ("v1", "v2"):
                with lock:
                    ready.add(ev.scope_id)
                    if ready == {"v1", "v2"}:
                        gate.write_text("go")  # 两个 victim 都就绪：放 crash job 崩

    grace = 2.0
    jobs = [_mode_job("c", "crash"), _mode_job("v1", "deaf"), _mode_job("v2", "deaf")]
    sink = _Sink()
    result = schedule(_rm(jobs), lambda name: engine, sink,
                      opts=ScheduleOpts(max_concurrency=3, fail_fast=True, grace_period_s=grace, heartbeat_interval_s=0))
    by = {jr.scope_id: jr for jr in result.jobs}
    assert (by["c"].status, by["c"].error_type) == (Status.ERROR, "engine_error")
    assert (by["v1"].status, by["v1"].error_type) == (Status.ABORTED, None) and (by["v2"].status, by["v2"].error_type) == (Status.ABORTED, None)
    # 耗时从 crash job 的 ScopeDone 之后、即它退出触发 _stop_all 起算不可得，改从「放行」时刻起算：放行到 run 结束的时间约等于一份宽限
    elapsed = time.time() - gate.stat().st_mtime  # 文件 mtime 是墙钟，不能与 monotonic 相减
    assert grace <= elapsed < 2 * grace - 0.2, elapsed  # 串行逐个等宽限至少要两份


def _assert_process_gone(pid: int, within_s: float = 5.0) -> None:
    import os

    deadline = time.monotonic() + within_s
    while time.monotonic() < deadline:
        try:
            os.kill(pid, 0)
        except ProcessLookupError:
            return
        time.sleep(0.1)
    raise AssertionError(f"进程 {pid} 仍存活")


def _kill_quietly(pid: int) -> None:
    import os
    import signal as _signal

    try:
        os.kill(pid, _signal.SIGKILL)
    except ProcessLookupError:
        pass


def test_concurrent_stop_calls_on_same_handle_are_safe():
    """同一 handle 的两次 stop 重叠（主线程的批量停与 worker 线程收尾时的幂等停）：都正常返回、不抛，进程被回收。"""
    import threading

    engine = _engine("deaf")
    handle, events = engine.run_scope(_job("s"))
    assert next(iter(events)).type == "scope_started"
    errors: list[BaseException] = []

    def stop():
        try:
            handle.stop(0.5)
        except BaseException as e:  # noqa: BLE001
            errors.append(e)

    barrier = threading.Barrier(2)
    spans: dict[int, tuple[float, float]] = {}

    def stop_at_barrier(i: int):
        barrier.wait(timeout=5.0)  # 两个线程同一刻发起
        t0 = time.monotonic()
        stop()
        spans[i] = (t0, time.monotonic())

    threads = [threading.Thread(target=stop_at_barrier, args=(i,)) for i in range(2)]
    for t in threads:
        t.start()
    for t in threads:
        t.join(timeout=5.0)
    assert not any(t.is_alive() for t in threads) and not errors, errors
    # 两次调用确实重叠：后开始的在先结束的之前开始（deaf worker 让每次 stop 至少阻塞满宽限）
    assert max(s[0] for s in spans.values()) < min(s[1] for s in spans.values()), spans
    proc = handle._proc  # type: ignore[attr-defined]
    assert proc.wait(timeout=3.0) is not None and proc.returncode != 0


def test_done_then_deaf_fdholder_hits_drain_bound_and_is_judged_timeout(tmp_path):
    """强杀后事件管道仍不 EOF（孙进程持有写端）：reader 线程永远读不到 EOF，schedule 只能在排空上界到点结束消费、按退出码未知
    回判——deadline 已过记 timeout；耗时落在宽限加余量之后，不挂死。"""
    import os

    from gherkai_core.schedule import DRAIN_MARGIN_S

    pid_file = tmp_path / "pid"
    engine = SubprocessEngine(cmd=[sys.executable, _WORKER],
                              env={**os.environ, "WORKER_MODE": "done_then_deaf_fdholder", "WORKER_PID_FILE": str(pid_file)})
    grace = 0.5
    t0 = time.monotonic()
    try:
        result = schedule(_rm([_job("s", timeout_s=1.0)]), lambda name: engine, CollectSink(),
                          opts=ScheduleOpts(grace_period_s=grace, heartbeat_interval_s=0.2))
        elapsed = time.monotonic() - t0
        jr = result.jobs[0]
        assert (jr.status, jr.error_type) == (Status.ERROR, "timeout"), (jr.status, jr.error_type, jr.message)
        assert grace + DRAIN_MARGIN_S <= elapsed < grace + DRAIN_MARGIN_S + 8.0, elapsed  # 等到了排空上界、之后不再等
        pids = [int(x) for x in pid_file.read_text().split()]
        assert len(pids) == 2
        _assert_process_gone(pids[0])  # worker 本体已被 SIGKILL
    finally:
        for line in (pid_file.read_text().split() if pid_file.exists() else []):
            _kill_quietly(int(line))  # 回收持有写端的孙进程（测试夹具自己的责任）


def test_done_then_deaf_worker_is_killed_after_hurry_exit_and_judged_timeout(tmp_path):
    """内容完整（scope_done 已到）后 worker 挂死且无视 SIGTERM：deadline 到点催停 → 宽限耗尽 SIGKILL → 管道 EOF、负退出码 →
    非干净退出不算内容完整，按首次仲裁回判 timeout（与无状态路径的 timed_out 一致）；不挂死。"""
    import os

    pid_file = tmp_path / "pid"
    engine = SubprocessEngine(cmd=[sys.executable, _WORKER], env={**os.environ, "WORKER_MODE": "done_then_deaf", "WORKER_PID_FILE": str(pid_file)})
    t0 = time.monotonic()
    result = schedule(_rm([_job("s", timeout_s=1.0)]), lambda name: engine, CollectSink(),
                      opts=ScheduleOpts(grace_period_s=0.5, heartbeat_interval_s=0.2))
    elapsed = time.monotonic() - t0
    jr = result.jobs[0]
    assert (jr.status, jr.error_type) == (Status.ERROR, "timeout"), (jr.status, jr.error_type, jr.message)
    assert [sr.status for sr in jr.scenarios] == [Status.PASSED]  # 内容已完整的明细保留
    # 走的是 SIGKILL 后管道 EOF 的路，不是排空上界兜底：耗时远小于 deadline 加宽限加余量，且 worker 进程已被回收
    assert elapsed < 4.5, elapsed
    _assert_process_gone(int(pid_file.read_text().split()[0]))


def test_done_then_slow_worker_keeps_content_verdict_despite_deadline():
    """内容完整后收尾拖过预算、被催停后协作以 0 退出：判定按内容（PASSED），不记超时（ADR 0034 机制二「内容完整后不再仲裁」）。"""
    engine = _engine("done_then_slow")
    t0 = time.monotonic()
    result = schedule(_rm([_job("s", timeout_s=1.0)]), lambda name: engine, CollectSink(),
                      opts=ScheduleOpts(grace_period_s=5.0, heartbeat_interval_s=0.2))
    elapsed = time.monotonic() - t0
    jr = result.jobs[0]
    assert (jr.status, jr.error_type) == (Status.PASSED, None), (jr.status, jr.error_type, jr.message)
    assert elapsed < 10.0, elapsed


def test_bad_event_line_stops_the_still_running_worker(tmp_path):
    """事件行解析失败（worker 违约）后 worker 还活着：schedule 记未知退出、并向它发停止请求，进程被回收、不留孤儿。"""
    import os

    pid_file = tmp_path / "pid"
    env = {**os.environ, "WORKER_MODE": "bad_line", "WORKER_PID_FILE": str(pid_file)}
    engine = SubprocessEngine(cmd=[sys.executable, _WORKER], env=env)
    result = schedule(_rm([_job("s")]), lambda name: engine, CollectSink(),
                      opts=ScheduleOpts(grace_period_s=5.0, heartbeat_interval_s=0.2))
    jr = result.jobs[0]
    assert (jr.status, jr.error_type) == (Status.ERROR, "engine_error") and jr.message.startswith("worker 异常：")
    pid = int(pid_file.read_text().split()[0])
    deadline = time.monotonic() + 5.0
    while time.monotonic() < deadline:
        try:
            os.kill(pid, 0)
        except ProcessLookupError:
            break
        time.sleep(0.1)
    else:
        raise AssertionError(f"worker 进程 {pid} 在停止请求后仍存活")


# ---- ADR 0028「会话血缘随首事件回传」条：session_id 经 scope_started 提前回传 → 超时/中止 scope_done 缺席时仍记得到血缘 ----
def test_session_id_captured_from_scope_started_on_timeout():
    engine = _engine("silent")
    result = schedule(
        _rm([_job("s", timeout_s=1.0)]), lambda name: engine, CollectSink(),
        opts=ScheduleOpts(grace_period_s=5.0),
    )
    # silent worker 超时被杀、从未 emit scope_done——但 session_id 已随 scope_started 落到 result（ADR 0028）
    assert result.jobs[0].status == Status.ERROR
    assert result.jobs[0].session_id == "echo-sess", "超时路径下 session_id 应仍从 scope_started 捕获到"


# ---- 同条直接验证：scope_started 事件本身带 sessionId（协议层，不经超时）----
def test_scope_started_carries_session_id():
    engine = _engine("silent")
    handle, events = engine.run_scope(_job("s"))
    first = next(iter(events))  # adapter 事件流是纯 Event（心跳在 schedule 层，不在此）
    assert isinstance(first, ScopeStarted)
    assert first.session_id == "echo-sess"
    handle.stop(grace_period_s=5.0)  # 收尾杀掉 silent worker


def test_large_job_and_noisy_worker_do_not_deadlock():
    """pump 线程必须**先于**写 stdin 起：job JSON >64KB（DocString）× worker 读 stdin 前先吐 >64KB stdout 噪声，
    否则父卡 stdin.write（管道满）、子卡 stdout.write（无人读）互锁——把两行 Thread.start() 挪回 stdin 之后，本用例
    在真子进程下挂死、由 pytest 全局 --timeout 判红（macOS/Linux 管道缓冲 64KB，两侧各取 300KB 留足余量）。"""
    import os
    env = {**os.environ, "WORKER_MODE": "pass", "WORKER_NOISE_BYTES": str(300_000)}
    engine = SubprocessEngine(cmd=[sys.executable, _WORKER], env=env)
    big = Step(0, "Given", "大参数", argument=StepArgument(kind="docString", content="y" * 300_000))
    job = Job(scope_id="s", scope_name="s", engine="novaact",
              scenarios=(Scenario(id="s:0", name="sc", steps=(big, Step(1, "When", "搜索"), Step(2, "Then", "进入页面"))),))
    _handle, events = engine.run_scope(job)
    types = [e.type for e in events]
    assert types[0] == "scope_started" and types[-1] == "scope_done" and types.count("step_done") == 3


def test_log_sink_receives_worker_logs_and_keeps_stderr_clean(capsys):
    """log_sink（ADR 0041 决策二）：给了文件句柄，worker 的 stdout/stderr 透传全写 sink（无颜色码）、本进程 stderr 不再出现
    `[worker …]` 行——`run --quiet` 靠它把 SDK 噪声挡在 agent 的上下文之外。"""
    import io
    import os

    sink = io.StringIO()
    env = {**os.environ, "WORKER_MODE": "pass", "WORKER_NOISE_BYTES": "64"}
    engine = SubprocessEngine(cmd=[sys.executable, _WORKER], env=env, log_sink=sink)
    handle, events = engine.run_scope(_job("s"))
    assert [e.type for e in events][-1] == "scope_done"
    deadline = time.monotonic() + 5
    while "[worker s:out]" not in sink.getvalue() and time.monotonic() < deadline:
        time.sleep(0.02)  # pump 是 daemon 线程，等它把噪声行写完
    assert "[worker s:out] " + "x" * 64 in sink.getvalue()
    assert "[worker" not in capsys.readouterr().err


def test_pump_log_masks_tunnel_credentials_in_sink_and_stderr(capsys):
    """worker 日志逐行转发时盖住隧道凭据（ADR 0035 决策 5）：写 log_sink 与写本进程 stderr 两条分支都要盖。

    直接喂 `_pump_log` 一个行迭代器：转发线程怎么接上这个函数已由上面那条真子进程用例覆盖，这里只锁逐行改写。"""
    import io

    from gherkai_core.adapters.subprocess_engine import _pump_log

    lines = ["navigate to https://u1:p1@h.example/login\n", "plain line\n"]
    sink = io.StringIO()
    _pump_log(iter(lines), "s", "err", sink)
    assert sink.getvalue() == ("[worker s:err] navigate to https://***@h.example/login\n"
                               "[worker s:err] plain line\n")

    _pump_log(iter(lines), "s", "out")   # 不给 sink：写本进程 stderr（capsys 下不是终端，不上色）
    err = capsys.readouterr().err
    assert "u1:p1@" not in err
    assert "[worker s:out] navigate to https://***@h.example/login\n" in err


# ---- worker 日志前缀的颜色（ADR 0047）：只标来源 scope、按 job 启动顺序分配、不含红绿、开关走统一策略 ----
import pytest as _pytest


@_pytest.fixture(autouse=True)
def _color_env_independent(monkeypatch):
    """本模块的颜色断言不受运行测试的 shell 影响：清掉 NO_COLOR / FORCE_COLOR / TERM=dumb，让「是否终端」成为唯一变量。"""
    for k in ("NO_COLOR", "FORCE_COLOR"):
        monkeypatch.delenv(k, raising=False)
    if monkeypatch.__class__ and __import__("os").environ.get("TERM") == "dumb":
        monkeypatch.delenv("TERM", raising=False)
    from gherkai_core.adapters import subprocess_engine as se
    se._reset_scope_colors()
    yield
    se._reset_scope_colors()


def test_scope_colors_assigned_in_order_without_collision_and_stable():
    from gherkai_core.adapters import subprocess_engine as se

    scopes = [f"features/x.feature:{n}" for n in (6, 16, 24, 33, 41, 50, 62, 70)]
    colors = [se._scope_color(s) for s in scopes]
    assert len(set(colors)) == len(scopes) == len(se._ANSI_COLORS)   # 前 8 个 scope 互不撞色
    assert colors == list(se._ANSI_COLORS)                            # 按首次出现顺序依次取色
    assert [se._scope_color(s) for s in scopes] == colors             # 同一 scope 恒同色
    assert se._scope_color("features/x.feature:99") == se._ANSI_COLORS[0]  # 第 9 个起循环


def test_palette_excludes_verdict_and_default_colors():
    """红绿留给判定语义（通过绿 / 失败红），白与默认色留给 core 自身的行。"""
    from gherkai_core.adapters import subprocess_engine as se

    assert not {31, 91, 32, 92, 37, 39, 97} & set(se._ANSI_COLORS)
    assert len(se._ANSI_COLORS) == 8


def test_pump_log_colors_prefix_only_when_policy_says_so(monkeypatch, capsys):
    from gherkai_core.adapters import subprocess_engine as se

    # capsys 下 stderr 不是终端：默认不上色
    se._pump_log(iter(["a\n"]), "s1", "err")
    assert capsys.readouterr().err == "[worker s1:err] a\n"

    # FORCE_COLOR 非空：非终端也上色，色码来自注册表（不上色的那次不占色，s2 是首个登记的 scope、取第一色）
    monkeypatch.setenv("FORCE_COLOR", "1")
    se._pump_log(iter(["b\n"]), "s2", "out")
    err = capsys.readouterr().err
    assert err == f"\033[{se._ANSI_COLORS[0]}m[worker s2:out]\033[0m b\n"

    # 调用方给定的 color 优先（run_scope 在 job 启动时取色、两条流同色）
    se._pump_log(iter(["c\n"]), "s2", "err", None, se._ANSI_COLORS[3])
    assert capsys.readouterr().err == f"\033[{se._ANSI_COLORS[3]}m[worker s2:err]\033[0m c\n"

    # NO_COLOR 非空：即使 FORCE_COLOR 也在，也不上色
    monkeypatch.setenv("NO_COLOR", "1")
    se._pump_log(iter(["d\n"]), "s2", "err")
    assert capsys.readouterr().err == "[worker s2:err] d\n"
