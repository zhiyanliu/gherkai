"""job 生命周期态 + severity 单测（ADR 0031）：skipped/aborted/pending/running、severity 序、_aggregate 过滤。

纯逻辑 + 内存假 Engine（不起子进程），验证 fail-fast 下两类「没跑成」被正确区分。
"""
from __future__ import annotations

import threading

from core.model import (
    ScenarioStarted,
    ScopeStarted,
    Status,
    StepDone,
    Votes,
    _NON_VERDICT,
    _STATUS_SEVERITY,
    severity,
)
from core.model import Job, JobResult
from core.schedule import ScheduleOpts, _aggregate, schedule
from core.serialize import job_result_from_dict, job_result_to_dict
from tests.fake_engine import CollectSink, FakeEngine, FakeResolver, FakeWorkerHandle
from tests.test_schedule import _IncClock, _job, _passing_events, _rm


# ---- serialize round-trip 覆盖新态（ADR 0031 touch-point）----
def test_new_states_round_trip():
    # Status(str,Enum) 接受新字符串，JobResult round-trip 自动支持——补单测护住，免回归
    for st in (Status.SKIPPED, Status.ABORTED, Status.PENDING, Status.RUNNING):
        job = Job(scope_id="s", scope_name="s", engine="midscene", scenarios=())
        back = job_result_from_dict(job_result_to_dict(JobResult(job=job, status=st)))
        assert back.status == st


# ---- severity 数值序（ADR 0031 决定二）----
def test_severity_order_fixes_string_sort_trap():
    # 钉死 'error' < 'failed' 字母序反向坑：severity 上 error 必须 > failed
    assert severity(Status.ERROR) > severity(Status.FAILED) > severity(Status.PASSED)
    # 但字符串字母序是反的（证明「绝不拿 Status 字符串比大小」的必要性）
    assert Status.ERROR.value < Status.FAILED.value  # 'error' < 'failed' 字母序——若拿它比 severity 就错了


def test_severity_skipped_lightest_aborted_heaviest():
    sev = _STATUS_SEVERITY
    assert sev[Status.SKIPPED] == min(sev.values())   # skipped 最轻（没执行，最该被无视）
    assert sev[Status.ABORTED] == max(sev.values())   # aborted 最重（有现场，最该被人看）


def test_pending_running_have_no_severity():
    # 前置态不是判定结论，无 severity（查表即编程错误）
    for st in (Status.PENDING, Status.RUNNING):
        try:
            severity(st)
            assert False, f"{st} 不该有 severity"
        except KeyError:
            pass


def test_non_verdict_filter_set():
    # 过滤名单 = 派生终态 + 前置态（ADR 0031 决定三）
    assert _NON_VERDICT == frozenset(
        {Status.SKIPPED, Status.ABORTED, Status.PENDING, Status.RUNNING}
    )


# ---- _aggregate 入口过滤（ADR 0031 决定三）----
def test_aggregate_filters_non_verdict():
    # 只有 skipped/aborted/pending/running → 过滤后空 → passed（不被这些态污染）
    assert _aggregate([Status.SKIPPED, Status.ABORTED]) == Status.PASSED
    assert _aggregate([Status.PENDING, Status.RUNNING]) == Status.PASSED
    # error 仍穿透：一个 error + 一堆非终态 → error
    assert _aggregate([Status.PASSED, Status.SKIPPED, Status.ERROR, Status.RUNNING]) == Status.ERROR
    # failed 穿透：passed + failed + skipped → failed
    assert _aggregate([Status.PASSED, Status.FAILED, Status.SKIPPED]) == Status.FAILED


def test_aggregate_all_skipped_no_error_not_misjudged_passed():
    # 防御：未来若引入非-fail-fast 的 skip，「全 skipped 无 error」不该被误判（过滤后空=passed，但至少不崩、语义明确）
    assert _aggregate([Status.SKIPPED, Status.SKIPPED]) == Status.PASSED


# ---- fail-fast：排队没起 → SKIPPED（worker 从未 spawn）----
def test_fail_fast_queued_job_is_skipped():
    # max_concurrency=1 串行：crash 先跑→崩→set abort_flag→第二个 job 还在排队→起跑前命中 abort 检查→SKIPPED
    jobs = [_job("crash"), _job("queued")]
    engine = FakeEngine(
        behaviors={
            "crash": _passing_events("crash", "crash:0"),
            "queued": _passing_events("queued", "queued:0"),
        },
        crash_after={"crash": 0},  # crash 立刻崩
    )
    result = schedule(
        _rm(jobs), FakeResolver(engine), CollectSink(),
        opts=ScheduleOpts(max_concurrency=1, fail_fast=True),
    )
    crash_jr = next(jr for jr in result.jobs if jr.scope_id == "crash")
    queued_jr = next(jr for jr in result.jobs if jr.scope_id == "queued")
    assert crash_jr.status == Status.ERROR          # 触发者：自身崩
    assert queued_jr.status == Status.SKIPPED       # 被牵连、worker 从未 spawn
    assert queued_jr.error_type is None             # skipped 无错（可无脑重跑）
    assert engine.run_count.get("queued") is None   # 关键：queued 的 worker 从未被 run_scope（没花钱）
    assert result.status == Status.ERROR            # run 级仍 error（crash 顶上去），skipped 不污染


# 死锁逃生用的宽松超时（秒）：远大于正常执行（~0.01s），仅防「放行信号因逻辑 bug 永不到来」时测试永久挂死。
# **正常路径绝不该触及它**——用它的两个夹具（_AbortProbeEngine / _NetRaiseEngine）都配了后置断言校验确被真正
# 放行（gate_released=True），超时（False）视为测试失败，绝不让超时静默退化成误判（本文件两个 fail-fast 夹具
# 曾各有一条此类残留 flaky：短超时兜底打破「被放行 ⟺ abort_flag 已 set」耦合，对抗验证暴露后统一改无限等 + 断言）。
_DEADLOCK_ESCAPE_S = 30.0


# ---- fail-fast：跑一半被掐 → ABORTED（已 spawn、有现场）----
# 标准 FakeEngine 在被 stop 时「协作式干净返回」→偏向 passed，且并发下 victim 常在 crash 崩之前/之后被
# SKIPPED，无法确定性命中 ABORTED 分支。故用一个小专用 engine 确定性复现「已 spawn、跑到一半、收到 stop
# 后仍越过 abort 检查」：victim 先吐一个事件（已有现场）→ 阻塞等 crash 崩并 set abort_flag → 再吐事件，
# 让 schedule 的事件间 abort 检查（schedule.py 的 abort_flag 分支）确定性命中 → ABORTED。
class _AbortProbeEngine:
    def __init__(self) -> None:
        self.handles: dict[str, FakeWorkerHandle] = {}
        self.run_count: dict[str, int] = {}
        self.crashed = threading.Event()   # crash 已崩并（由 schedule）set 了 abort_flag
        self.victim_started = threading.Event()  # victim 已吐过首个事件（已有现场）
        self.gate_released = False  # victim 是否被真正放行（True）而非死锁逃生超时（False）——供测试后置断言

    def run_scope(self, job):
        h = FakeWorkerHandle()
        self.handles[job.scope_id] = h
        self.run_count[job.scope_id] = self.run_count.get(job.scope_id, 0) + 1
        return h, self._gen(job, h)

    def _gen(self, job, handle):
        if job.scope_id == "crash":
            self.victim_started.wait(timeout=_DEADLOCK_ESCAPE_S)  # 先让 victim 起来、吐出首事件，保证它"已 spawn 有现场"
            raise RuntimeError("crash 立刻崩")    # schedule 收到→记 error→set abort_flag
        # victim：吐首事件（建立现场）→ 等 crash 崩 + abort 生效 → 之后**持续**吐事件（不因 handle.stopped
        # 提前收尾）。关键（去 flake）：schedule 的 abort 检查在**事件间**（下一次迭代的循环顶），故 abort 生效后
        # 必须还有下一个事件被 next() 拉出来、触发那次检查 → 命中 abort 分支 → ABORTED。若像原来只吐一个 StepDone
        # 就自然结束（或一醒来见 stopped 就 return），for 可能在 abort 检查前 StopIteration 正常收尾 → 误判 PASSED。
        # schedule 命中 abort 分支后 return、不再 next() 本生成器，故不会真跑满 range（1000 只是防御性上限）。
        yield ScenarioStarted(scenario_id="victim:0")
        self.victim_started.set()
        # 接近无限等（_DEADLOCK_ESCAPE_S 仅死锁逃生）：**不用短超时兜底**——短超时会打破「被放行 ⟺ abort_flag
        # 已 set」的耦合：极端饥饿下 wait 超时先于 _stop_all 返回，victim 带 abort_flag=False 继续吐 StepDone →
        # abort 检查读 False → 一路吐完自然收尾 → 误判 PASSED（与姊妹测试 test_network_error_during_abort 同源的
        # 残留 flaky，对抗验证暴露）。gate_released 记录是否真放行（非超时逃生）供测试后置断言，杜绝超时静默退化。
        self.gate_released = self.crashed.wait(timeout=_DEADLOCK_ESCAPE_S)
        for i in range(1000):
            yield StepDone(scenario_id="victim:0", step_index=i, status=Status.PASSED, votes=Votes(3, 3))


def test_fail_fast_inflight_job_is_aborted():
    engine = _AbortProbeEngine()
    jobs = [_job("crash"), _job("victim")]

    # 放行信号必须精确对应「abort_flag 已 set」。踩过的坑：crash 崩溃时 schedule 会 self._stop() 停**它自己**的
    # handle（schedule.py except 分支），这早于主线程 _stop_all() 的 abort_flag.set()——若见任意 stop 就放行，
    # victim 会在 abort_flag 还是 False 时醒来吐事件、一路查到 False → 误判 PASSED（flaky 根因）。
    # 正解：只在 **victim 自己的 handle** 被 stop 时才放行——victim 的 handle 只由 _stop_all() 停，那时 abort_flag 必已 set。
    orig_stop = FakeWorkerHandle.stop

    def stop_hook(self, grace_period_s):
        if self is engine.handles.get("victim"):  # 只认 victim 被停（= _stop_all，abort_flag 已 set），不认 crash 自停
            engine.crashed.set()
        return orig_stop(self, grace_period_s)

    FakeWorkerHandle.stop = stop_hook
    try:
        result = schedule(
            _rm(jobs), FakeResolver(engine), CollectSink(),
            opts=ScheduleOpts(max_concurrency=2, fail_fast=True, grace_period_s=0.1),
        )
    finally:
        FakeWorkerHandle.stop = orig_stop

    # 前置校验：victim 确被真正放行（crashed.set()，= _stop_all 已 abort_flag.set()），而非死锁逃生超时——
    # 后者意味着「被放行 ⟺ abort_flag 已 set」耦合被超时旁路打破，此时 ABORTED 断言即便偶过也不可信。
    assert engine.gate_released, "victim 未被真正放行（crashed 超时），耦合被打破——测试环境异常，非有效断言"
    victim_jr = next(jr for jr in result.jobs if jr.scope_id == "victim")
    assert engine.run_count.get("victim") == 1     # 已 spawn（区别于 skipped 的从未 spawn）
    assert victim_jr.status == Status.ABORTED        # 跑一半被 fail-fast 掐
    assert victim_jr.error_type is None              # aborted 不带 errorType（不是引擎故障，是被叫停）
    assert victim_jr.status != Status.ERROR          # 关键回归：被牵连中止绝不再记成 error（ADR 0031）
    assert result.status == Status.ERROR             # run 级仍 error（crash 顶上去），aborted 不进 run 级聚合


# ---- severity 完整传递序（ADR 0031 决定二）：一行钉死全序，抗中间调换回归 ----
def test_severity_full_chain():
    # 现有 test_severity_* 只验两端极值 + 中间三态；这里钉死完整 5 态传递序
    assert (severity(Status.SKIPPED) < severity(Status.PASSED) < severity(Status.FAILED)
            < severity(Status.ERROR) < severity(Status.ABORTED))


def test_aggregate_running_does_not_pollute_clean_pass():
    # 干净的 [PASSED, RUNNING]：running 被滤掉、不把结果带偏 → PASSED（ADR 0031 决定三）
    assert _aggregate([Status.PASSED, Status.RUNNING]) == Status.PASSED
    # 空集兜底（schedule docstring「空也算 passed」）
    assert _aggregate([]) == Status.PASSED


# ---- WorkerNetworkError 竞态块按 abort_flag 拆分（ADR 0031 决定一，最易回归的坑）----
# schedule.py 的 except WorkerNetworkError 块有三子分支：abort_flag→ABORTED / 超时→error+timeout / else→network_error。
# 这是 ADR 用整段文字警告的坑（self_stopped 被 timeout/fail-fast 共用、要看 abort_flag）。现有 network 测试只命中
# else 分支，timeout 测试命中的是事件循环里的 deadline 而非 network 块里的重判——故专门复现这两条竞态子分支。
from core.errors import WorkerNetworkError  # noqa: E402


class _NetRaiseEngine:
    """victim job 的 worker：等一个 gate 放行后才抛 WorkerNetworkError（模拟「建连退避期间」被中止/超时后退 80）。
    crash job：立刻崩，让 schedule set abort_flag（fail-fast 场景用）。

    **确定性同步（去 flake 关键）**：victim 对 gate 用**接近无限**的等待（_DEADLOCK_ESCAPE_S，仅作死锁逃生），
    **不用短超时兜底**——短超时会打破「被放行 ⟺ abort_flag 已 set」的耦合：极端调度饥饿下 wait 超时先于
    _stop_all 返回，victim 带 abort_flag=False 往下抛 → 误落 network_error（实测 ~0.8% 残留 flaky，对抗验证
    暴露）。改无限等 + 后置断言 gate 确被放行后，「被放行」与「abort_flag 已 set」由 _stop_all 的程序序
    （先 set 后 stop）刚性耦合，无超时旁路。crash 的 entered.wait 同理放宽。gate_released 记录放行事实供断言。"""
    def __init__(self, gate: threading.Event, set_on_victim_entry: threading.Event | None = None):
        self.handles: dict = {}
        self.run_count: dict = {}
        self._gate = gate
        self._entered = set_on_victim_entry
        self.gate_released = False  # victim 是否被真正放行（True）而非死锁逃生超时（False）——供测试后置断言

    def run_scope(self, job):
        h = FakeWorkerHandle()
        self.handles[job.scope_id] = h
        self.run_count[job.scope_id] = self.run_count.get(job.scope_id, 0) + 1
        return h, self._gen(job)

    def _gen(self, job):
        if job.scope_id == "crash":
            # crash 必须等 victim 先进入事件循环（过了起跑前 abort 检查）才崩——否则 victim 会被判 SKIPPED 而非 ABORTED
            if self._entered is not None:
                self._entered.wait(timeout=_DEADLOCK_ESCAPE_S)
            raise RuntimeError("crash 崩 → set abort_flag")
        # victim：先吐一个事件证明已 spawn、在事件循环里（过了起跑前检查）；宣告 entered；
        # 再 wait gate（被 fail-fast stop 时放行）→ 抛网络码 → 命中 except WorkerNetworkError 块的 abort 分支。
        yield ScopeStarted(scope_id="victim", session_id="sess-v")
        if self._entered is not None:
            self._entered.set()
        # 接近无限等（仅死锁逃生）：正常必被 gate.set() 唤醒。记录是否真放行（非超时）供断言。
        self.gate_released = self._gate.wait(timeout=_DEADLOCK_ESCAPE_S)
        raise WorkerNetworkError("victim 建连失败、以网络码退出")


def test_network_error_during_abort_is_aborted_not_network():
    # 竞态：worker 已在事件循环里、abort_flag 已 set 后才抛 WorkerNetworkError → 走 abort 分支 → ABORTED（非 network_error）
    gate = threading.Event()
    entered = threading.Event()
    engine = _NetRaiseEngine(gate, set_on_victim_entry=entered)
    # victim 被 stop 时（schedule fail-fast → 调 handle.stop）放行 gate，让它在 abort 已生效后才抛网络码。
    # **只认 victim 自己的 handle.stop**——否则 crash 崩溃时它 except 里的 self._stop() 也会触发本 hook、
    # 提前 set gate（那发生在主线程 _stop_all 的 abort_flag.set() 之前），victim 会在 abort_flag 未 set 时
    # 就抛 WorkerNetworkError → 误落 network_error 分支（曾致本测试 ~44% 误判，根因是共享 gate 被计划外路径放行）。
    orig_stop = FakeWorkerHandle.stop

    def stop_hook(self, grace_period_s):
        if self is engine.handles.get("victim"):  # 仅 victim 的 stop（fail-fast 真正掐 victim 时，此刻 abort_flag 必已 set）放行
            gate.set()
        return orig_stop(self, grace_period_s)

    FakeWorkerHandle.stop = stop_hook
    try:
        result = schedule(
            _rm([_job("crash"), _job("victim")]), FakeResolver(engine), CollectSink(),
            opts=ScheduleOpts(max_concurrency=2, fail_fast=True, grace_period_s=0.1),
        )
    finally:
        FakeWorkerHandle.stop = orig_stop
    # 前置校验：victim 确被真正放行（gate.set()），而非死锁逃生超时——后者意味着「被放行 ⟺ abort_flag 已 set」
    # 的耦合被超时旁路打破，此时下面的 ABORTED 断言即便偶然通过也不可信。钉死这一条，杜绝超时静默退化。
    assert engine.gate_released, "victim 未被真正放行（gate 超时），耦合被打破——测试环境异常，非有效断言"
    victim_jr = next(jr for jr in result.jobs if jr.scope_id == "victim")
    assert victim_jr.status == Status.ABORTED          # abort 分支优先：不记成 network_error
    assert victim_jr.error_type is None                # aborted 不带 errorType


def test_network_error_during_timeout_is_timeout_not_aborted():
    # 竞态：单 job，worker 在建连退避里以网络码退出，但此刻墙钟已过 deadline → 走 timeout 分支 → error+timeout（非 aborted、非 network_error）
    gate = threading.Event(); gate.set()  # 立刻放行：victim 一进来就抛网络码
    engine = _NetRaiseEngine(gate)
    # _IncClock 每读 +10s，job_timeout=5 → schedule 内首次读 clock 建 deadline≈10，网络块重判 clock()>deadline 必真
    clock = _IncClock(10.0)
    result = schedule(
        _rm([_job("victim", timeout_s=5.0)]), FakeResolver(engine), CollectSink(),
        opts=ScheduleOpts(clock=clock, network_retry=0),
    )
    victim_jr = result.jobs[0]
    assert victim_jr.status == Status.ERROR
    assert victim_jr.error_type == "timeout"           # 超时不被网络码绕过、不归 aborted
