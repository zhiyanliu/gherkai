"""schedule 模块（ADR 0026）：Job[] → 并发跑 → 收流式事件 → RunResult。

job 间并行（maxConcurrency 上限）、失败隔离（默认）/ fail-fast（可配）、超时兜底、优雅停。
schedule 只下逻辑「停」（handle.stop(grace)），不懂信号/进程——机制藏在 Engine adapter（ADR 0026）。

并发模型：每个 worker 一个线程，ThreadPoolExecutor(max_workers=maxConcurrency) 自然限制
同时在跑的 worker 数（= 同时活的 AgentCore 会话数，保护真实成本）。worker 线程内迭代 0024 事件流、
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
        job = self.job
        result = JobResult(scope_id=job.scope_id, status=Status.PASSED)
        scenario_status: dict[str, Status] = {}
        # 时长追踪（core 用事件到达时间戳算墙钟，ADR 0024；clock 与超时复用同一注入时钟）：
        timing = _Timing()

        # 起 worker 前先看是否已被 fail-fast 中止（排队中的 job 不该再起、不烧钱）
        if self.abort_flag.is_set():
            result.status = Status.ERROR
            result.error_type = "engine_error"
            result.message = "fail-fast：批次已中止，未启动"
            return result

        try:
            engine = self.engines(job.engine)
            self.handle, events = engine.run_scope(job)
        except Exception as e:  # 起 worker 失败（spawn 失败等）
            result.status = Status.ERROR
            result.error_type = "engine_error"
            result.message = f"起 worker 失败：{e}"
            return result

        deadline = (self.opts.clock() + self.opts.job_timeout_s) if self.opts.job_timeout_s else None
        clock = self.opts.clock

        try:
            for event in events:
                # 事件间检查：超时 / fail-fast → 优雅停 worker（ADR 0026）
                if deadline is not None and clock() > deadline:
                    self._stop()
                    result.status = Status.ERROR
                    result.error_type = "timeout"
                    result.message = f"job 超时（>{self.opts.job_timeout_s}s）"
                    return result
                if self.abort_flag.is_set():
                    self._stop()
                    result.status = Status.ERROR
                    result.error_type = "engine_error"
                    result.message = "fail-fast：其他 job 失败，本 job 被中止"
                    return result

                self._emit(event)
                self._reduce(event, result, scenario_status, timing, clock())
        except Exception as e:  # worker 迭代中崩（异常退出）
            self._stop()
            result.status = Status.ERROR
            result.error_type = "engine_error"
            result.message = f"worker 异常：{e}"
            return result

        # 正常跑完：job 状态 = 各 scenario 归约
        result.status = _aggregate(list(scenario_status.values()))
        return result

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
    jobs: list[Job],
    engines: EngineResolver,
    sink: Sink,
    opts: ScheduleOpts | None = None,
) -> RunResult:
    """跑一批 job → RunResult（ADR 0026）。

    engines: 按 job.engine 解析 Engine 的 resolver（schedule 对腿数/腿名无知）。
    sink:    接收 0024 原始流式事件的回调（与 RunResult 是同一事件流的两个视图）。
    """
    opts = opts or ScheduleOpts()
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
        status=run_status, jobs=job_results,
        total_tokens=sum(tok) if tok else None,
        total_time_worked_s=sum(tw) if tw else None,
        duration_ms=run_duration_ms,
    )
