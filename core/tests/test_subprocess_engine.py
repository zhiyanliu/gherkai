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
    engine = SubprocessEngine(cmd=[sys.executable, _WORKER],
                              env={**os.environ, "WORKER_MODE": "pass", "WORKER_CRASH_AFTER_FILE": str(gate), "WORKER_LOCK_DIR": str(tmp_path)})
    ready: set[str] = set()
    lock = threading.Lock()

    class _Sink(CollectSink):
        def __call__(self, ev):
            super().__call__(ev)
            if isinstance(ev, ScopeStarted) and ev.scope_id in ("v1", "v2", "c"):
                with lock:
                    ready.add(ev.scope_id)
                    if ready == {"v1", "v2", "c"}:
                        gate.write_text("go")  # 两个 victim 与 crash job 都已就绪：放 crash job 崩（它在 scenario_started 之后等这个文件）

    grace = 3.0
    jobs = [_mode_job("c", "crash"), _mode_job("v1", "deaf"), _mode_job("v2", "deaf")]
    sink = _Sink()
    stop_phase_start: list[float] = []

    def on_job_complete(jr):
        # crash job 的判定回调紧接着就是主线程的 _stop_all：从这里起算（crash job 自己退出时的日志收尾等待发生在它之前）
        if jr.scope_id == "c":
            stop_phase_start.append(time.monotonic())

    # 只量「victim 进程何时死掉」：victim 启动时在 <scope>.lock 上持有 flock，内核在它退出那一刻释放锁；测试线程轮询非阻塞加锁、
    # 加到即死亡时刻。按 pid 轮询不行：强杀后到被回收之前进程是僵尸、kill(pid, 0) 仍成功，而回收发生在 reader 读到 EOF、
    # 日志线程收尾之后——那些等待与并行无关，不能混进度量。锁文件由 victim 先在临时名上加锁再改名，出现即已上锁、无空读竞态。
    import fcntl
    import threading as _threading
    deaths: dict[str, float] = {}

    def watch(scope_id: str):
        lock_file = tmp_path / f"{scope_id}.lock"
        while not lock_file.exists():
            time.sleep(0.02)
        fd = os.open(lock_file, os.O_RDONLY)
        try:
            while True:
                try:
                    fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
                except BlockingIOError:
                    time.sleep(0.02)
                    continue
                deaths[scope_id] = time.monotonic()
                return
        finally:
            os.close(fd)

    watchers = [_threading.Thread(target=watch, args=(s,), daemon=True) for s in ("v1", "v2")]
    for t in watchers:
        t.start()
    result = schedule(_rm(jobs), lambda name: engine, sink, on_job_complete=on_job_complete,
                      opts=ScheduleOpts(max_concurrency=3, fail_fast=True, grace_period_s=grace, heartbeat_interval_s=0))
    for t in watchers:
        t.join(timeout=5.0)
    by = {jr.scope_id: jr for jr in result.jobs}
    assert (by["c"].status, by["c"].error_type) == (Status.ERROR, "engine_error")
    assert (by["v1"].status, by["v1"].error_type) == (Status.ABORTED, None) and (by["v2"].status, by["v2"].error_type) == (Status.ABORTED, None)
    assert len(stop_phase_start) == 1 and set(deaths) == {"v1", "v2"}, deaths
    spans = {s: deaths[s] - stop_phase_start[0] for s in deaths}
    # 并行停：两个 victim 都在约一份宽限后被强杀；串行逐个等宽限时后一个至少两份
    assert all(grace - 0.3 <= v for v in spans.values()), spans
    assert max(spans.values()) < 2 * grace - 0.3, spans


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


def _wait_pids(pid_file, n: int, within_s: float = 5.0) -> list[int]:
    """等 pid 文件里出现至少 n 行（孙进程由它自己登记，可能比父进程晚一点）；到时返回当前已有的。"""
    deadline = time.monotonic() + within_s
    while True:
        pids = [int(x) for x in pid_file.read_text().split()] if pid_file.exists() else []
        if len(pids) >= n or time.monotonic() >= deadline:
            return pids
        time.sleep(0.05)


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
        pids = _wait_pids(pid_file, 2)
        assert len(pids) == 2, pids  # 父进程与孙进程各一行（孙进程自己登记，父进程被强杀也不丢）
        _assert_process_gone(pids[0])  # worker 本体已被 SIGKILL
    finally:
        for pid in _wait_pids(pid_file, 2):  # 孙进程的 pid 由它自己写入：轮询等它登记完再回收（测试夹具自己的责任）
            _kill_quietly(pid)


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


# ---- 进程组与所属进程号（ADR 0024 终止契约「使用方中断」「父进程消失」条）----

def _wait_dead(pid: int, timeout_s: float = 5.0) -> bool:
    """等到 pid 不再存在（已被回收）。"""
    import os
    deadline = time.monotonic() + timeout_s
    while time.monotonic() < deadline:
        try:
            os.kill(pid, 0)
        except ProcessLookupError:
            return True
        time.sleep(0.05)
    return False


# 包装进程（模拟定位链里 uvx / npx 这类进程）：用 Python 而不是 sh 起孙进程——POSIX 规定非交互 shell 的异步命令在任何显式重定向之前就把
# stdin 指向 /dev/null，dash（Linux 的 sh）照此执行，`"$0" "$1" <&0 &` 里的 `<&0` 复制到的已是 /dev/null，孙进程读不到 job（CI 实遇；
# macOS 的 sh 不这样做，本机测试过了）。Python 的 Popen 缺省继承 stdin、stdout、stderr，事件管道按 EVENTS_FD 显式继承。
_WRAPPER_WAIT = ("import os, subprocess, sys; p = subprocess.Popen(sys.argv[1:], pass_fds=[int(os.environ['EVENTS_FD'])]); "
                 "sys.exit(p.wait())")  # 组长等孙进程结束（uvx / npx 的常态）
_WRAPPER_EXIT = ("import os, subprocess, sys; subprocess.Popen(sys.argv[1:], pass_fds=[int(os.environ['EVENTS_FD'])]); "
                 "sys.exit(0)")  # 组长起完孙进程立即退出（组长先于 worker 消失的形态）


def _wrapper_engine(mode: str, wrapper: str, pid_file: str) -> SubprocessEngine:
    """经包装进程起假 worker：真正的 worker 是孙进程。wrapper 取 _WRAPPER_WAIT 或 _WRAPPER_EXIT。"""
    import os
    env = {**os.environ, "WORKER_MODE": mode, "WORKER_PID_FILE": pid_file}
    return SubprocessEngine(cmd=[sys.executable, "-c", wrapper, sys.executable, _WORKER], env=env)


def _grandchild_pid(pid_file: str) -> int:
    return int(Path(pid_file).read_text(encoding="utf-8").split()[0])


def test_worker_env_carries_owner_pid():
    """起 worker 时传入所属进程号 GHERKAI_PARENT_PID（取值为本进程 pid）：worker 据此核验所属进程是否存活。"""
    import os
    script = ("import os,sys,json; sys.stdin.readline(); fd=int(os.environ['EVENTS_FD']); "
              "os.write(fd, (json.dumps({'type':'scope_started','scopeId':'s','sessionId':os.environ['GHERKAI_PARENT_PID']})+'\\n').encode())")
    engine = SubprocessEngine(cmd=[sys.executable, "-c", script])
    _handle, events = engine.run_scope(_job("s"))
    evs = list(events)
    assert evs and evs[0].type == "scope_started"
    assert evs[0].session_id == str(os.getpid())


def test_force_stop_kills_whole_group_behind_wrapper(tmp_path):
    """零宽限的停止对整个进程组发 SIGKILL：包装进程是组长、worker 是孙进程时，孙进程同样被结束（否则它仍持有事件管道）。"""
    import os
    pid_file = str(tmp_path / "pids")
    engine = _wrapper_engine("deaf", _WRAPPER_WAIT, pid_file)
    handle, events = engine.run_scope(_job("s"))
    assert next(events).type == "scope_started"  # worker 已起、pid 文件已写
    worker_pid = _grandchild_pid(pid_file)
    assert worker_pid != handle._proc.pid  # 确是孙进程
    handle.stop(0.0)
    assert _wait_dead(worker_pid), "孙进程（真正的 worker）应被整组 SIGKILL 结束"
    handle._proc.wait(timeout=5)
    try:
        os.killpg(handle._proc.pid, 0)
        assert False, "进程组应已不存在"
    except ProcessLookupError:
        pass


def test_force_stop_kills_grandchild_after_leader_exited(tmp_path):
    """组长（包装进程）已退出、孙进程仍在：零宽限停止不以组长是否退出为条件，仍对整组发 SIGKILL。"""
    pid_file = str(tmp_path / "pids")
    engine = _wrapper_engine("deaf", _WRAPPER_EXIT, pid_file)
    handle, events = engine.run_scope(_job("s"))
    assert next(events).type == "scope_started"
    handle._proc.wait(timeout=5)  # 组长已退出
    worker_pid = _grandchild_pid(pid_file)
    assert not _wait_dead(worker_pid, 0.3)  # 孙进程还活着（无视 SIGTERM 的形态，只有 SIGKILL 能结束它）
    handle.stop(0.0)
    assert _wait_dead(worker_pid), "组长退出后孙进程仍应被整组 SIGKILL 结束"


def test_cooperative_stop_signals_whole_group_behind_wrapper(tmp_path):
    """协作停止的 SIGTERM 也发给整组：worker 不靠包装进程转发信号就能收到并走协作退出。"""
    pid_file = str(tmp_path / "pids")
    engine = _wrapper_engine("hang", _WRAPPER_WAIT, pid_file)
    handle, events = engine.run_scope(_job("s"))
    assert next(events).type == "scope_started"
    worker_pid = _grandchild_pid(pid_file)
    t0 = time.monotonic()
    handle.stop(5.0)
    assert _wait_dead(worker_pid), "孙进程应因收到 SIGTERM 协作退出"
    assert time.monotonic() - t0 < 4.0  # 没有等到宽限耗尽才 SIGKILL


def test_positive_grace_stop_kills_deaf_grandchild_after_grace_behind_wrapper(tmp_path):
    """正宽限的停止等的是整组消失：组长（包装进程）被 SIGTERM 结束后，无视 SIGTERM 的孙进程在宽限到期时被整组 SIGKILL。"""
    pid_file = str(tmp_path / "pids")
    engine = _wrapper_engine("deaf", _WRAPPER_WAIT, pid_file)
    handle, events = engine.run_scope(_job("s"))
    assert next(events).type == "scope_started"
    worker_pid = _grandchild_pid(pid_file)
    t0 = time.monotonic()
    handle.stop(1.0)
    assert _wait_dead(worker_pid), "孙进程应在宽限到期后被整组 SIGKILL 结束"
    elapsed = time.monotonic() - t0
    assert 1.0 <= elapsed < 4.0, elapsed  # 等满宽限才强杀，之后不再多等


def test_positive_grace_stop_kills_deaf_grandchild_when_leader_already_exited(tmp_path):
    """组长已退出、无视 SIGTERM 的孙进程仍在：正宽限的停止不因组长已退出而跳过，宽限到期整组 SIGKILL。"""
    pid_file = str(tmp_path / "pids")
    engine = _wrapper_engine("deaf", _WRAPPER_EXIT, pid_file)
    handle, events = engine.run_scope(_job("s"))
    assert next(events).type == "scope_started"
    handle._proc.wait(timeout=5)  # 组长已退出
    worker_pid = _grandchild_pid(pid_file)
    handle.stop(1.0)
    assert _wait_dead(worker_pid), "组长退出后孙进程仍应在宽限到期后被结束"
