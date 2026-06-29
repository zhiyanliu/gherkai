"""schedule 模块（ADR 0026）：Job[] → 并发跑 → 收流式事件 → RunResult。

job 间并行（maxConcurrency 上限）、失败隔离（默认）/ fail-fast（可配）、超时兜底、优雅停。
schedule 只下逻辑「停」（handle.stop(grace)），不懂信号/进程——机制藏在 Engine adapter（ADR 0026）。

并发模型：每个 worker 一个线程，ThreadPoolExecutor(max_workers=maxConcurrency) 自然限制
同时在跑的 worker 数（= 同时活的 AgentCore 会话数，保护真实成本）。worker 线程内迭代 ADR 0024 事件流、
转 sink、归约成 JobResult。

超时/fail-fast 用**事件间检查**：每收一个事件后查 (clock.now()-start > jobTimeout) 或 abort_flag，
命中则 handle.stop(grace) 让 worker 退出。注入 clock 使这两条路径可确定性单测。
注：完全无事件输出的「死等」由 Engine adapter 的读超时兜底（subprocess pipe read deadline），
schedule 这层覆盖「有事件但进展过慢」——分层职责（ADR 0026）。
"""
from __future__ import annotations

import threading
import time as _time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from typing import Callable

from core.model import (
    Event,
    Job,
    JobResult,
    RunMeta,
    RunResult,
    ScenarioDone,
    ScenarioResult,
    ScenarioStarted,
    ScopeDone,
    ScopeStarted,
    Status,
    StepDone,
    StepResult,
    StepStarted,
)
from core.errors import WorkerNetworkError
from core.ports import EngineResolver, Sink


@dataclass
class _Timing:
    """单个 worker 跑批中各级起始时间戳 + 暂存的 step 结果（core 算墙钟时长用，ADR 0024）。"""

    scope_start: float | None = None
    scenario_start: dict[str, float] = field(default_factory=dict)
    step_start: dict[tuple[str, int], float] = field(default_factory=dict)
    steps: dict[str, list[StepResult]] = field(default_factory=dict)  # scenario_id → 暂存 StepResult


@dataclass
class ScheduleOpts:
    max_concurrency: int = 4  # 同时在跑的 worker 上限（保护真实 AWS 成本/配额）
    fail_fast: bool = False  # 任一 job 崩是否中止整批
    job_timeout_s: float | None = None  # per-job 墙钟超时（None=不超时）
    grace_period_s: float = 5.0  # 停止请求后等 worker 优雅退出的宽限秒
    clock: Callable[[], float] = _time.monotonic  # 时间源（可注入 fake clock 测超时/grace 路径）
    # 网络瞬时故障的 job 级重试（ADR 0028）：仅对 error_type==network_error 且「会话未起（零 step_done）」
    # 的 job 重试整批。默认 0=关（本地 smoke 不需要；CI/抖动环境可开）。
    network_retry: int = 0  # 额外重试次数（总尝试 = network_retry + 1）
    retry_sleep: Callable[[float], None] = _time.sleep  # 重试间隔（可注入 no-op，保 fake-clock 单测纯净）


def _aggregate(statuses: list[Status]) -> Status:
    """状态归约：任一 error→error；任一 failed→failed；否则 passed（空也算 passed）。"""
    if any(s == Status.ERROR for s in statuses):
        return Status.ERROR
    if any(s == Status.FAILED for s in statuses):
        return Status.FAILED
    return Status.PASSED


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
    ) -> None:
        self.job = job
        self.engines = engines
        self.sink = sink
        self.sink_lock = sink_lock
        self.opts = opts
        self.abort_flag = abort_flag
        self.handle = None  # 暴露给 fail-fast：其他 job 崩时外部可 stop 本 worker

    def run(self) -> JobResult:
        """跑一个 job，含网络瞬时故障的选择性重试（ADR 0028）。

        重试门槛（双条件 AND，绝不放宽）：① 本次以 network_error 失败（worker 建连失败、
        重试耗尽）② 「会话未起」= 本次零 step_done（证明 act 没跑、无副作用、不烧重复钱）。
        fail_fast/timeout 优先级高于 network 重试（它们已主动中止，不再重跑）。
        """
        # deadline 跨 attempt 共享（ADR 0028）：覆盖所有 attempt 之和，重试不重置——否则 N 次重试
        # 各拿一整份 job_timeout、绕过超时上限。run 级算一次，所有 _run_once 共用。
        deadline = (self.opts.clock() + self.opts.job_timeout_s) if self.opts.job_timeout_s else None
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
        return last  # 重试耗尽，返回最后一次（network_error）

    def _run_once(self, deadline: float | None) -> tuple[JobResult, bool, bool]:
        """单次执行 job。返回 (JobResult, 是否 network_error, 是否 emit 过 step_done)。

        deadline：run 级共享的超时截止（None=不超时）；跨 attempt 不重置（ADR 0028）。
        """
        job = self.job
        result = JobResult(job=job, status=Status.PASSED)
        scenario_status: dict[str, Status] = {}
        saw_step = False  # 是否观察到 step_done（会话已起、act 可能有副作用 → 不可 job 级重试，ADR 0028）
        self_stopped = False  # schedule 主动停了本 worker（timeout/fail-fast）→ 其后的退出码不当 network（ADR 0028）
        # 时长追踪（core 用事件到达时间戳算墙钟，ADR 0024；clock 与超时复用同一注入时钟）：
        timing = _Timing()

        # 起 worker 前先看是否已被 fail-fast 中止（排队中的 job 不该再起、不烧钱）
        if self.abort_flag.is_set():
            result.status = Status.ERROR
            result.error_type = "engine_error"
            result.message = "fail-fast：批次已中止，未启动"
            return result, False, saw_step

        try:
            engine = self.engines(job.engine)
            self.handle, events = engine.run_scope(job)
        except Exception as e:  # 起 worker 失败（spawn 失败等）
            result.status = Status.ERROR
            result.error_type = "engine_error"
            result.message = f"起 worker 失败：{e}"
            return result, False, saw_step

        clock = self.opts.clock

        try:
            for event in events:
                # 事件间检查：超时 / fail-fast → 优雅停 worker（ADR 0026）。
                # 这两条优先于 network 重试：已主动中止的 job 不再重跑（ADR 0028）。
                if deadline is not None and clock() > deadline:
                    self_stopped = True
                    self._stop()
                    result.status = Status.ERROR
                    result.error_type = "timeout"
                    result.message = f"job 超时（>{self.opts.job_timeout_s}s）"
                    return result, False, saw_step
                if self.abort_flag.is_set():
                    self_stopped = True
                    self._stop()
                    result.status = Status.ERROR
                    result.error_type = "engine_error"
                    result.message = "fail-fast：其他 job 失败，本 job 被中止"
                    return result, False, saw_step

                if isinstance(event, StepDone):
                    saw_step = True  # 会话已起、有 act 执行 → 封掉 job 级重试（防重复副作用）
                self._emit(event)
                self._reduce(event, result, scenario_status, timing, clock())
        except WorkerNetworkError as e:  # 建连失败、重试耗尽（ADR 0028）：可被 job 级重试
            self._stop()
            result.status = Status.ERROR
            # 竞态防护（ADR 0028）：worker 卡在建连退避里不吐事件时，上面的 timeout/abort 分支没机会执行
            # （for-event 阻塞在读），worker 最终退 80 直达此处。故在此**重新判**超时/fail-fast：
            # 若墙钟已超 / 已被 fail-fast 中止，则这是「主动中止」语义，记 timeout/engine_error、**不重试**
            # （主动中止优先于 network 重试），不能让超时预算被建连退避绕过。
            if self_stopped or self.abort_flag.is_set():
                result.error_type = "engine_error"
                result.message = f"worker 被主动停止（fail-fast）后以网络码退出：{e}"
                return result, False, saw_step
            if deadline is not None and clock() > deadline:
                result.error_type = "timeout"
                result.message = f"job 超时（>{self.opts.job_timeout_s}s）——建连退避期间超时"
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

        # 正常跑完：job 状态 = 各 scenario 归约
        result.status = _aggregate(list(scenario_status.values()))
        return result, False, saw_step

    def _emit(self, event: Event) -> None:
        with self.sink_lock:  # 多 worker 并发 → 串行化 sink 调用（sink 实现不必线程安全）
            self.sink(event)

    def _reduce(
        self, event: Event, result: JobResult, scenario_status: dict[str, Status],
        timing: "_Timing", now: float,
    ) -> None:
        # started 事件：记各级起始时间戳（now = 事件到达 core 的墙钟，ADR 0024）
        if isinstance(event, ScopeStarted):
            timing.scope_start = now
        elif isinstance(event, ScenarioStarted):
            timing.scenario_start[event.scenario_id] = now
        elif isinstance(event, StepStarted):
            timing.step_start[(event.scenario_id, event.step_index)] = now
        elif isinstance(event, StepDone):
            # 兜底：若某 scenario 有 step error 但无 scenario_done，仍记一笔（取最严重）
            cur = scenario_status.get(event.scenario_id)
            if event.status == Status.ERROR or (event.status == Status.FAILED and cur != Status.ERROR):
                scenario_status[event.scenario_id] = event.status
            # 累加 step 成本到 scope 级（ADR 0024）：core 只合计 engine 报的原生量、不算美元。
            cost = event.cost
            if cost is not None:
                if cost.tokens is not None:
                    result.total_tokens = (result.total_tokens or 0) + cost.tokens
                if cost.time_worked_s is not None:
                    result.total_time_worked_s = (result.total_time_worked_s or 0.0) + cost.time_worked_s
            # step 墙钟时长（step_started→此刻）+ 暂存 StepResult，待 scenario_done 挂入
            st = timing.step_start.get((event.scenario_id, event.step_index))
            dur_ms = (now - st) * 1000.0 if st is not None else None
            timing.steps.setdefault(event.scenario_id, []).append(
                StepResult(index=event.step_index, status=event.status,
                           duration_ms=dur_ms, votes=event.votes, error_type=event.error_type)
            )
        elif isinstance(event, ScenarioDone):
            scenario_status[event.scenario_id] = event.status
            ss = timing.scenario_start.get(event.scenario_id)
            result.scenarios.append(
                ScenarioResult(
                    scenario_id=event.scenario_id,
                    status=event.status,
                    steps=timing.steps.get(event.scenario_id, []),
                    duration_ms=(now - ss) * 1000.0 if ss is not None else None,
                    report_refs=event.report_refs,
                )
            )
        elif isinstance(event, ScopeDone):
            result.session_id = event.session_id
            if event.report_refs:
                result.report_refs = result.report_refs + event.report_refs
            if timing.scope_start is not None:
                result.duration_ms = (now - timing.scope_start) * 1000.0

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
) -> RunResult:
    """跑一次 run（RunMeta = definition）→ RunResult（ADR 0026）。

    run_meta: 一次 run 的 definition（run_id + created_at + jobs），由组合根生成 run_id + plan
              产出 jobs 后构造传入（schedule 不自己生成 id、不取时钟——保 fake-clock 可确定性单测的
              纯归约定位；WebUI「提交即返回 runId」也要求 definition 先于跑批存在，ADR 0027）。
              schedule 原样把 run_meta 放进 RunResult（definition + 判定的合成），不从结果反推身份。
    engines:  按 job.engine 解析 Engine 的 resolver（schedule 对腿数/腿名无知）。
    sink:     接收 ADR 0024 原始流式事件的回调（与 RunResult 是同一事件流的两个视图）。
    """
    opts = opts or ScheduleOpts()
    jobs = list(run_meta.jobs)
    sink_lock = threading.Lock()
    abort_flag = threading.Event()
    workers = [
        _Worker(job, engines, sink, sink_lock, opts, abort_flag) for job in jobs
    ]

    run_start = opts.clock()  # run 级墙钟起点（整体包住，含并发）
    job_results: list[JobResult] = []
    with ThreadPoolExecutor(max_workers=max(1, opts.max_concurrency)) as pool:
        future_to_worker = {pool.submit(w.run): w for w in workers}
        for future in as_completed(future_to_worker):
            jr = future.result()
            job_results.append(jr)
            # fail-fast：一个 job 崩（error）→ 中止整批：设 abort + stop 所有在跑 worker（ADR 0026）
            if opts.fail_fast and jr.status == Status.ERROR and not abort_flag.is_set():
                abort_flag.set()
                for w in workers:
                    w._stop()
    run_duration_ms = (opts.clock() - run_start) * 1000.0

    # 还原成 jobs 输入顺序（as_completed 是完成序），稳定输出
    order = {job.scope_id: i for i, job in enumerate(jobs)}
    job_results.sort(key=lambda jr: order.get(jr.scope_id, 0))

    run_status = _aggregate([jr.status for jr in job_results])
    # 成本归约（ADR 0024）：core 只各自合计 engine 报的原生量，不算美元、不判可信度。
    #   total_tokens / total_time_worked_s = 跨 job 求和；None=无腿报这个量（不假装 0）。
    tok = [jr.total_tokens for jr in job_results if jr.total_tokens is not None]
    tw = [jr.total_time_worked_s for jr in job_results if jr.total_time_worked_s is not None]
    return RunResult(
        run_meta=run_meta,
        status=run_status, jobs=job_results,
        total_tokens=sum(tok) if tok else None,
        total_time_worked_s=sum(tw) if tw else None,
        duration_ms=run_duration_ms,
    )
