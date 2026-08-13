"""schedule 模块（ADR 0026）：Job[] → 并发跑 → 收流式事件 → RunResult。

job 间并行（maxConcurrency 上限）、失败隔离（默认）/ fail-fast（可配）、超时兜底、优雅停。
schedule 只下逻辑「停」（handle.stop(grace)），不懂信号/进程——机制藏在 Engine adapter（ADR 0026）。

并发模型：每个 worker 一个线程，ThreadPoolExecutor(max_workers=maxConcurrency) 自然限制
同时在跑的 worker 数（= 同时活的 AgentCore 会话数，保护真实成本）。worker 线程内迭代 ADR 0024 事件流、
转 sink、归约成 JobResult。

超时/fail-fast 用**事件间检查**：每收一个事件（或 _heartbeat_wrap 的存活心跳）后查 (clock.now()-start >
jobTimeout) 或 abort_flag，命中则 handle.stop(grace) 让 worker 退出。注入 clock 使这两条路径可确定性单测。
注：worker 完全静默（卡在单次操作内、不吐事件）时，靠 _heartbeat_wrap（后台 reader 线程 + queue 超时，
ADR 0028）周期性 yield `_HEARTBEAT` 让本循环醒来查超时——否则裸 for-event 阻塞在读上、超时永不触发
（曾致 300s 超时拖到 ~620s 才被外层杀）。心跳在 schedule 层做一次、对所有 adapter 通用，端口保持纯
`Iterator[Event]`（不渗实现细节，ADR 0026）。心跳不归约、跳过即可。
"""
from __future__ import annotations

import threading
import time as _time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from typing import Callable

from core.model import (
    Event,
    Job,
    JobResult,
    RunMeta,
    RunResult,
    ScopeDone,
    Status,
    StepDone,
)
from core.errors import WorkerNetworkError
from core.ports import EngineResolver, JobSink, Sink
from core.project import Timing as _Timing, _aggregate as _project_aggregate, reduce_event

import queue as _queue


class _Heartbeat:
    """存活心跳哨兵（schedule 私有，ADR 0028）：worker 活着但暂时没吐事件时，_heartbeat_wrap 注入它，
    让 _run_once 的事件循环醒来查 deadline/abort。**不是领域 Event**——不进 model/ports/wire，不归约、不 emit。
    """


_HEARTBEAT = _Heartbeat()


def _heartbeat_wrap(events, poll_interval_s, deadline):
    """把 adapter 的纯 `Iterator[Event]` 包成「事件 + 静默心跳」流（ADR 0026/0028）。

    单线程无法在 `next(events)` 阻塞于管道读时被定时器唤醒，故把内层迭代搬到一个**后台 reader 线程**：
    它 `for ev in events: q.put(ev)`，把事件（及内层抛出的异常）塞进队列；本生成器主侧 `q.get(timeout)`——
    超时没拿到（worker 静默卡死）就 yield `_HEARTBEAT`，拿到事件就 yield 事件，拿到异常就 raise（透传给
    schedule 的 except，保 WorkerNetworkError/ValueError 分类不变）。

    **为何在 schedule 层做一次、而非每个 worker/adapter**：心跳是「超时消费方（schedule 持有 deadline）对任何
    慢/静默流的通用兜底」，与引擎无关；放这里写一次，对子进程/未来 Fargate/内存 FakeEngine 全适用，端口保持
    纯 `Iterator[Event]`（不渗实现细节）。事件正常流动时 q.get 即时返回、永不注入心跳——故 fake-clock 单测的
    clock 读取序列不变（reader 线程只搬事件、绝不读 clock）。

    poll_interval_s<=0 或 deadline is None（不超时）时，退化为直接转发内层（不起线程、零开销，保留既有行为）。
    """
    # 不需要心跳的场景（无超时上限）：直接转发，省一个线程（也让无 deadline 的既有路径行为完全不变）。
    if deadline is None or poll_interval_s <= 0:
        yield from events
        return

    q: _queue.Queue = _queue.Queue()

    def _reader():
        try:
            for ev in events:
                q.put(("ev", ev))
        except BaseException as e:  # noqa: BLE001  内层任何异常（含 WorkerNetworkError）透传给主侧重抛
            q.put(("exc", e))
            return
        q.put(("done", None))

    t = threading.Thread(target=_reader, daemon=True)
    t.start()
    try:
        while True:
            try:
                kind, payload = q.get(timeout=poll_interval_s)
            except _queue.Empty:
                yield _HEARTBEAT  # 静默：让 _run_once 醒来查 deadline/abort（ADR 0028）
                continue
            if kind == "ev":
                yield payload
            elif kind == "exc":
                raise payload  # 透传内层异常（schedule 的 except WorkerNetworkError/Exception 据此分类）
            else:  # done：内层正常迭代完（adapter 的事件流自然终止，engine 无关，ADR 0024/0026）——
                   # subprocess 是管道 EOF+proc.wait returncode 0；Fargate 无论走 scope_done 主判还是 STOPPED 兜底，都
                   # 等 DescribeTasks STOPPED 读 exitCode（与 subprocess 无条件 proc.wait() 同构，ADR 0024「事件流结束信号」），
                   # 其中 exit>0 经 _raise_for_exit 走上面的 exc 分支、唯 exit==0 落此 done。
                return
    finally:
        # 主侧不再拉取（schedule 主动 stop/超时后放弃本生成器）：reader 线程仍可能阻塞在 next(events) 上，
        # 靠 schedule 已调的 handle.stop() 让 adapter 侧终止事件流解除其阻塞（subprocess：SIGTERM→worker 退出→
        # 管道 EOF；Fargate：StopTask→DescribeTasks STOPPED→迭代器停）。daemon 线程不挡进程退出；这里不 join
        # （避免在 stop 尚未生效时阻塞 schedule），与既有「放弃 generator」语义一致。engine 无关（ADR 0026）。
        pass


@dataclass
class ScheduleOpts:
    max_concurrency: int = 4  # 同时在跑的 worker 上限（保护真实 AWS 成本/配额）
    fail_fast: bool = False  # 任一 job 崩是否中止整批
    grace_period_s: float = 5.0  # 停止请求后等 worker 优雅退出的宽限秒
    # grace 下限（引擎无关的纯数，ADR 0024 grace 硬约束）：调用方（组合根）声明「本 run 的 grace 至少要这么大」，
    # schedule 起 worker 前 enforce grace_period_s >= min_grace_s。**core 不认这个下限从何而来**（引擎特定的
    # 「Nova 需 ≥act_timeout+余量」由组合根算好传入）——core 只校验「传入 grace ≥ 声明下限」这个引擎无关的关系，
    # 保 core 纯 reducer/引擎无知（ADR 0016/0026）。默认 0.0=无下限（不破现有直接构造 ScheduleOpts 的调用方）。
    min_grace_s: float = 0.0
    clock: Callable[[], float] = _time.monotonic  # 时间源（可注入 fake clock 测超时/grace 路径）
    # 网络瞬时故障的 job 级重试（ADR 0028）：仅对 error_type==network_error 且「会话未起（零 step_done）」
    # 的 job 重试整批。默认 0=关（本地 smoke 不需要；CI/抖动环境可开）。
    network_retry: int = 0  # 额外重试次数（总尝试 = network_retry + 1）
    retry_sleep: Callable[[float], None] = _time.sleep  # 重试间隔（可注入 no-op，保 fake-clock 单测纯净）
    # 心跳轮询间隔（秒，ADR 0028）：worker 静默卡死（不吐事件）时，_heartbeat_wrap 每隔这么久让事件循环
    # 醒一次查 deadline/abort——否则裸迭代阻塞在读上、超时永不触发（曾致 300s 超时拖到 ~620s）。
    # 0.5s：足够细让 300s 级超时近准时，又不忙轮询。事件正常流动时不触发心跳（queue 即时拿到）。
    heartbeat_interval_s: float = 0.5


# 状态归约提炼到 core.project._aggregate（同步/无状态两路径共用一份，ADR 0034「不复制归约逻辑」——
# 同 reduce_event/_Timing 的提炼手法；此别名保 schedule 侧既有引用（含测试）不动）。
_aggregate = _project_aggregate


class _Worker:
    """单个 job 的执行体：跑在线程里，迭代事件流、转 sink、归约成 JobResult。"""

    def __init__(
        self,
        job: Job,
        engines: EngineResolver,
        sink: Sink,
        sink_lock: threading.Lock,
        opts: ScheduleOpts,
        abort_flag: threading.Event,
        on_event: Sink | None = None,
    ) -> None:
        self.job = job
        self.engines = engines
        self.sink = sink
        self.sink_lock = sink_lock
        self.opts = opts
        self.abort_flag = abort_flag
        # on_event：每个事件的旁路观察者（实时落库用），在 sink_lock **之外**调（故不把磁盘 RMW 串进进度显示临界区，
        # ADR 0030 决定三并发不变量；落库自身的线程安全由观察者自持锁保证，如 RunPersistence._lock）。
        self.on_event = on_event
        self.handle = None  # 暴露给 fail-fast：其他 job 崩时外部可 stop 本 worker

    def run(self) -> JobResult:
        """跑一个 job，含网络瞬时故障的选择性重试（ADR 0028）。

        重试门槛（双条件 AND，绝不放宽）：① 本次以 network_error 失败（worker 建连失败、
        重试耗尽）② 「会话未起」= 本次零 step_done（证明 act 没跑、无副作用、不烧重复钱）。
        fail_fast/timeout 优先级高于 network 重试（它们已主动中止，不再重跑）。
        """
        # deadline 跨 attempt 共享（ADR 0028）：覆盖所有 attempt 之和，重试不重置——否则 N 次重试
        # 各拿一整份 timeout、绕过超时上限。run 级算一次，所有 _run_once 共用。
        # 预算载体在 definition（Job.timeout_s，@timeout tag 或组合根缺省填充——ADR 0034「job timeout」节）。
        deadline = (self.opts.clock() + self.job.timeout_s) if self.job.timeout_s else None
        last: JobResult | None = None
        for attempt in range(self.opts.network_retry + 1):
            if attempt > 0:
                # 仅在「上次是 network_error 且会话未起」时走到这；退避用注入 sleep（保 fake-clock 纯净）
                self.opts.retry_sleep(min(2.0 * attempt, 4.0))
            result, is_network, saw_step = self._run_once(deadline)
            last = result
            # 可重试 = network_error + 会话未起（零 step_done）+ 未被 fail-fast 中止 + 还有重试额度
            retriable = (
                is_network
                and not saw_step
                and not self.abort_flag.is_set()
                and attempt < self.opts.network_retry
            )
            if not retriable:
                return result
        return last  # 不可达：循环末次迭代 retriable 必 False → 上面必 return；此处仅供类型收窄（否则视为可能隐式 return None）

    def _run_once(self, deadline: float | None) -> tuple[JobResult, bool, bool]:
        """单次执行 job。返回 (JobResult, 是否 network_error, 是否 emit 过 step_done)。

        deadline：run 级共享的超时截止（None=不超时）；跨 attempt 不重置（ADR 0028）。
        """
        job = self.job
        result = JobResult(job=job, status=Status.PASSED)
        scenario_status: dict[str, Status] = {}
        saw_step = False  # 是否观察到 step_done（会话已起、act 可能有副作用 → 不可 job 级重试，ADR 0028）
        saw_scope_done = False  # 是否见到 scope_done（内容完整，ADR 0024/0026——EOF 后落归约终态的前提）
        self_stopped = False  # schedule 主动停了本 worker（timeout/fail-fast）→ 其后的退出码不当 network（ADR 0028）
        # 时长追踪（core 用事件到达时间戳算墙钟，ADR 0024；clock 与超时复用同一注入时钟）：
        timing = _Timing()

        # 起 worker 前先看是否已被 fail-fast 中止（排队中的 job 不该再起、不烧钱）。
        # worker 从未 spawn → SKIPPED（没执行/没花钱/可无脑重跑，ADR 0031），非 error。
        if self.abort_flag.is_set():
            result.status = Status.SKIPPED
            result.error_type = None
            result.message = "fail-fast：批次已中止，未启动（worker 未 spawn）"
            return result, False, saw_step

        try:
            engine = self.engines(job.engine)
            self.handle, raw_events = engine.run_scope(job)
        except Exception as e:  # 起 worker 失败（spawn 失败等）
            result.status = Status.ERROR
            result.error_type = "engine_error"
            result.message = f"起 worker 失败：{e}"
            return result, False, saw_step

        clock = self.opts.clock
        # 包心跳（ADR 0028）：worker 静默卡死时让下面的事件循环能周期性醒来查 deadline/abort，
        # 而非永久阻塞在 next(raw_events) 的管道读上。无 deadline 时退化为直接转发（不起线程）。
        events = _heartbeat_wrap(raw_events, self.opts.heartbeat_interval_s, deadline)

        try:
            for event in events:
                # 事件间检查：超时 / fail-fast → 优雅停 worker（ADR 0026）。
                # 这两条优先于 network 重试：已主动中止的 job 不再重跑（ADR 0028）。
                if deadline is not None and clock() > deadline:
                    self_stopped = True
                    self._stop()
                    result.status = Status.ERROR
                    result.error_type = "timeout"
                    result.message = f"job 超时（>{self.job.timeout_s}s）"
                    return result, False, saw_step
                if self.abort_flag.is_set():
                    self_stopped = True
                    self._stop()
                    # 已 spawn、跑一半被 fail-fast 掐 → ABORTED（有副作用/有现场可查，ADR 0031），非 error。
                    # 注意与上面 timeout 分支区分：超时仍是 error+timeout，只有 abort_flag 触发的中止才 ABORTED。
                    result.status = Status.ABORTED
                    result.error_type = None
                    result.message = "fail-fast：其他 job 失败，本 job 被中止"
                    return result, False, saw_step

                # _Heartbeat = _heartbeat_wrap 的静默心跳（worker 卡住不吐事件时，让上面的 deadline/abort
                # 检查能周期性跑，ADR 0028）。不是领域事件、不 emit、不归约——查完超时即跳过，等下一个真事件或心跳。
                # 用 isinstance（而非 is _HEARTBEAT）使静态类型能把 event 收窄回 Event（消除下面 _emit/_reduce 的告警）。
                if isinstance(event, _Heartbeat):
                    continue

                if isinstance(event, StepDone):
                    saw_step = True  # 会话已起、有 act 执行 → 封掉 job 级重试（防重复副作用）
                if isinstance(event, ScopeDone):
                    saw_scope_done = True  # 内容完整信号（ADR 0024/0026：EOF 后落归约终态的前提）
                self._emit(event)
                if self.on_event is not None:
                    self.on_event(event)  # 旁路观察者：在 sink_lock 外调（实时落库不阻塞别的 worker 进度显示）
                self._reduce(event, result, scenario_status, timing, clock())
        except WorkerNetworkError as e:  # 建连失败、重试耗尽（ADR 0028）：可被 job 级重试
            self._stop()
            result.status = Status.ERROR
            # 竞态防护（ADR 0028）：worker 卡在建连退避里不吐事件时，上面的 timeout/abort 分支没机会执行
            # （for-event 阻塞在读），worker 最终退 80 直达此处。故在此**重新判**超时/fail-fast：
            # 若墙钟已超 / 已被 fail-fast 中止，则这是「主动中止」语义、**不重试**（主动中止优先于 network 重试），
            # 不能让超时预算被建连退避绕过。**按来源拆开**（ADR 0031）：fail-fast 中止→ABORTED，超时→error+timeout，
            # 看 abort_flag 而非笼统 self_stopped（self_stopped 被 timeout/fail-fast 共用）；abort 先判，故 abort 优先。
            if self.abort_flag.is_set():
                result.status = Status.ABORTED
                result.error_type = None
                result.message = f"worker 被 fail-fast 中止后以网络码退出：{e}"
                return result, False, saw_step
            if self_stopped or (deadline is not None and clock() > deadline):
                result.error_type = "timeout"
                result.message = f"job 超时（>{self.job.timeout_s}s）——建连退避期间超时"
                return result, False, saw_step
            result.error_type = "network_error"
            result.message = f"worker 建连失败（网络/SSL 瞬时故障）：{e}"
            return result, True, saw_step
        except Exception as e:  # worker 迭代中崩（其它异常退出）
            self._stop()
            result.status = Status.ERROR
            result.error_type = "engine_error"
            result.message = f"worker 异常：{e}"
            return result, False, saw_step

        # 事件流正常 EOF。落归约终态前先校验内容完整（ADR 0024「两件都要」在同步路径的落点，0026）：
        # worker 被协作停（fail-fast/timeout 的 handle.stop）后按契约不吐 in-flight 的 scenario_done/
        # scope_done、干净退出（exit 0）→ 流自然 EOF——不校验就直落归约，部分完成的 job 会拿已完成的
        # scenario 聚合出 PASSED（假绿）。未见 scope_done 按来源分流，对齐 project._job_status 口径。
        if not saw_scope_done:
            self._stop()
            if self.abort_flag.is_set():
                result.status = Status.ABORTED  # fail-fast 掐停（ADR 0031：跑一半被掐、有现场可查）
                result.error_type = None
                result.message = "fail-fast：其他 job 失败，本 job 被中止（worker 收停后干净退出）"
                return result, False, saw_step
            result.status = Status.ERROR
            if deadline is not None and clock() > deadline:
                result.error_type = "timeout"
                result.message = f"job 超时（>{self.job.timeout_s}s）——worker 收停后干净退出"
            else:
                result.error_type = "engine_error"
                result.message = "worker 干净退出但未发完 scope_done（内容不完整、进程却说成功=矛盾）"
            return result, False, saw_step

        # 正常跑完（内容完整）：job 状态 = 各 scenario 归约
        result.status = _aggregate(list(scenario_status.values()))
        return result, False, saw_step

    def _emit(self, event: Event) -> None:
        with self.sink_lock:  # 多 worker 并发 → 串行化 sink 调用（sink 实现不必线程安全）
            self.sink(event)

    def _reduce(
        self, event: Event, result: JobResult, scenario_status: dict[str, Status],
        timing: "_Timing", now: float,
    ) -> None:
        # 归约逻辑提炼到 core.project.reduce_event（同步 run 与无状态 submit 两路径共用一份，ADR 0034）。
        # 本方法保留为薄 delegate，不改行为（现有 test_schedule 为护栏）。
        reduce_event(event, result, scenario_status, timing, now)

    def _stop(self) -> None:
        if self.handle is not None:
            try:
                self.handle.stop(self.opts.grace_period_s)
            except Exception:
                pass  # stop 兜底失败不应掩盖原始结果


def schedule(
    run_meta: RunMeta,
    engines: EngineResolver,
    sink: Sink,
    opts: ScheduleOpts | None = None,
    on_job_complete: JobSink | None = None,
    on_event: Sink | None = None,
) -> RunResult:
    """跑一次 run（RunMeta = definition）→ RunResult（ADR 0026）。

    run_meta: 一次 run 的 definition（run_id + created_at + jobs），由组合根生成 run_id + plan
              产出 jobs 后构造传入（schedule 不自己生成 id、不取时钟——保 fake-clock 可确定性单测的
              纯归约定位；WebUI「提交即返回 runId」也要求 definition 先于跑批存在，ADR 0027）。
              schedule 原样把 run_meta 放进 RunResult（definition + 判定的合成），不从结果反推身份。
    engines:  按 job.engine 解析 Engine 的 resolver（schedule 对引擎数/引擎名无知）。
    sink:     接收 ADR 0024 原始流式事件的回调（与 RunResult 是同一事件流的两个视图）。被 sink_lock 串行化（进度显示）。
    on_job_complete: 每个 job 完成时回调它**已归约好的 JobResult**（ADR 0030 实时写接缝）。schedule 自己
              不碰任何 store——落库/写序由组合根注入的回调编排（默认 None=no-op，逃生舱：测试/--no-report/
              纯内存都不传，保 schedule 纯 reducer 与 fake-clock 可测）。**正常路径（产品）总会接 persistence**，
              None 不是常态。在 as_completed 主线程**串行** fire（非 worker 线程）。
    on_event: 每个事件的**旁路观察者**（实时落库 RUNNING 中间态用，ADR 0030）。与 sink 区别：on_event 在
              **sink_lock 之外**调——故落库的磁盘 RMW 不阻塞别的 worker 的进度显示（决定三并发不变量）。
              它仍在 worker 线程被调、多 worker 并发，故观察者须自持锁（如 RunPersistence._lock）。默认 None。
    """
    opts = opts or ScheduleOpts()
    # grace 硬约束（ADR 0024）：起任何 worker 前 enforce grace 合法且 ≥ 调用方声明的下限。
    # 引擎无关的纯关系校验——core 不认下限从何而来（组合根按引擎算好传入 min_grace_s）。任何前端都受此护栏。
    if opts.grace_period_s <= 0 or opts.grace_period_s < opts.min_grace_s:
        raise ValueError(
            f"grace_period_s={opts.grace_period_s} 非法：须 > 0 且 ≥ min_grace_s={opts.min_grace_s}"
            "（grace < 单 act 时长会致 SIGKILL 先于会话释放、软停失效、会话泄漏，ADR 0024 grace 硬约束）"
        )
    jobs = list(run_meta.jobs)
    sink_lock = threading.Lock()
    abort_flag = threading.Event()
    workers = [
        _Worker(job, engines, sink, sink_lock, opts, abort_flag, on_event=on_event) for job in jobs
    ]

    run_start = opts.clock()  # run 级墙钟起点（整体包住，含并发）
    job_results: list[JobResult] = []

    def _stop_all() -> None:
        abort_flag.set()
        for w in workers:
            w._stop()

    with ThreadPoolExecutor(max_workers=max(1, opts.max_concurrency)) as pool:
        future_to_worker = {pool.submit(w.run): w for w in workers}
        for future in as_completed(future_to_worker):
            jr = future.result()
            job_results.append(jr)
            # 实时写接缝（ADR 0030）：job 一完成即回调它已归约好的 JobResult，供组合根落库（schedule 不碰 store）。
            # 主线程串行 fire。默认 None=no-op。回调异常仍冒泡（落库失败=真问题），但**冒泡前先 stop 所有在跑
            # worker**——否则异常跳出 with、shutdown(wait=True) 会等在跑 worker 自然跑完（真 AgentCore 会话继续烧钱）。
            if on_job_complete is not None:
                try:
                    on_job_complete(jr)
                except BaseException:
                    _stop_all()  # 止血：掐掉在跑会话，别空烧
                    raise
            # fail-fast：一个 job 崩（error）→ 中止整批：设 abort + stop 所有在跑 worker（ADR 0026）
            if opts.fail_fast and jr.status == Status.ERROR and not abort_flag.is_set():
                _stop_all()
    run_duration_ms = (opts.clock() - run_start) * 1000.0

    # 还原成 jobs 输入顺序（as_completed 是完成序），稳定输出
    order = {job.scope_id: i for i, job in enumerate(jobs)}
    job_results.sort(key=lambda jr: order.get(jr.scope_id, 0))

    run_status = _aggregate([jr.status for jr in job_results])
    # 成本归约（ADR 0024）：core 只各自合计 engine 报的原生量，不算美元、不判可信度。
    #   total_tokens / total_time_worked_s = 跨 job 求和；None=无引擎报这个量（不假装 0）。
    tok = [jr.total_tokens for jr in job_results if jr.total_tokens is not None]
    tw = [jr.total_time_worked_s for jr in job_results if jr.total_time_worked_s is not None]
    return RunResult(
        run_meta=run_meta,
        status=run_status, jobs=job_results,
        total_tokens=sum(tok) if tok else None,
        total_time_worked_s=sum(tw) if tw else None,
        duration_ms=run_duration_ms,
    )
