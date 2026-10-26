"""内存假 Engine（测试夹具，ADR 0026「接口是测试面」）。

直接在进程内吐预设的 ADR 0024 事件流，不 spawn 子进程、不连 AgentCore。
支持：正常事件流、worker 崩（迭代中抛异常）、慢 worker（配合 fake clock 测超时）、记录 stop。
"""
from __future__ import annotations

import threading
from typing import Callable, Iterator

from gherkai_core.errors import WorkerExitError, WorkerNetworkError
from gherkai_core.model import Event, Job


class FakeWorkerHandle:
    def __init__(self, on_stop: Callable[[], None] | None = None) -> None:
        self.stopped = False
        self.stop_grace: float | None = None
        self._stop_event = threading.Event()  # 配了收尾事件的假 worker 在事件发完后等它（模拟 worker 活着、等被停）
        self._on_stop = on_stop  # 测试钩子：模拟真 stop() 阻塞消耗的时间（如推进假时钟）

    def stop(self, grace_period_s: float) -> None:
        self.stopped = True
        self.stop_grace = grace_period_s
        if self._on_stop is not None:
            self._on_stop()
        self._stop_event.set()

    def wait_stopped(self, timeout_s: float) -> bool:
        return self._stop_event.wait(timeout_s)


class FakeEngine:
    """按 job.scope_id → 预设事件流（或行为）吐事件。

    behaviors: scope_id -> 一个 callable(job) -> Iterator[Event]，或直接事件 list。
    crash_after: scope_id -> 在产出第 N 个事件后抛异常（模拟 worker 崩）。
    on_event: 每产出一个事件时调用的钩子（测试可在此推进 fake clock，模拟慢 worker）。
    """

    def __init__(
        self,
        behaviors: dict[str, list[Event] | Callable[[Job], Iterator[Event]]],
        crash_after: dict[str, int] | None = None,
        network_crash_after: dict[str, int] | None = None,
        on_event: Callable[[str, int], None] | None = None,
        tail_after_stop: dict[str, list[Event]] | None = None,
        exit_code: dict[str, int] | None = None,
        tail_delay_s: float = 0.0,
        hang_after_stop: set[str] | None = None,
        on_stop: Callable[[str], None] | None = None,
    ) -> None:
        self.behaviors = behaviors
        self.crash_after = crash_after or {}
        # network_crash_after: scope_id -> 第 N 个事件后抛 WorkerNetworkError（模拟建连失败，ADR 0028）。
        # N=0 模拟「会话未起就建连失败」（零事件）。每个 scope_id 的崩溃次数可用 list 表达递减（模拟重试后成功）。
        self.network_crash_after = network_crash_after or {}
        # tail_after_stop: scope_id -> 被 schedule 停止后仍吐出的收尾事件（模拟 worker 收 SIGTERM 后走终结四阶段、发
        # session_closed，ADR 0051 决策 5；core 须在停止后继续有界消费才收得到，ADR 0034 机制二）。
        # 键存在即表示「发完事件后活着等被停」（值可为空列表：等停、无收尾事件）；不配键的 scope 发完事件即 EOF。
        self.tail_after_stop = tail_after_stop or {}
        # exit_code: scope_id -> 事件流结束后以该非零退出码退出（抛 WorkerExitError，模拟 worker 发完事件又异常退出 / 被 SIGKILL）
        self.exit_code = exit_code or {}
        # tail_delay_s: 收到停止请求后隔多久才发收尾事件（模拟释放阶段耗时；配合实时钟测「先判 abort、收尾期间 deadline 才到」）
        self.tail_delay_s = tail_delay_s
        # hang_after_stop: 收到停止请求后卡死、永不 EOF（模拟收尾挂住的 worker；由 schedule 的排空上界兜底）
        self.hang_after_stop = hang_after_stop or set()
        # on_stop: handle.stop() 被调时的钩子（传 scope_id），模拟真 stop() 阻塞在 proc.wait(grace) 消耗的时间（测试里推进假时钟）
        self.on_stop = on_stop
        self.run_count: dict[str, int] = {}  # 每个 scope_id 被 run_scope 的次数（验证 job 级重试）
        self.on_event = on_event
        self.handles: dict[str, FakeWorkerHandle] = {}
        self._lock = threading.Lock()

    def run_scope(self, job: Job) -> tuple[FakeWorkerHandle, Iterator[Event]]:
        handle = FakeWorkerHandle(on_stop=(lambda: self.on_stop(job.scope_id)) if self.on_stop is not None else None)
        with self._lock:
            self.handles[job.scope_id] = handle
            attempt = self.run_count.get(job.scope_id, 0)
            self.run_count[job.scope_id] = attempt + 1
        return handle, self._gen(job, handle, attempt)

    def _gen(self, job: Job, handle: FakeWorkerHandle, attempt: int) -> Iterator[Event]:
        behavior = self.behaviors.get(job.scope_id, [])
        events = behavior(job) if callable(behavior) else iter(behavior)
        crash_at = self.crash_after.get(job.scope_id)
        # network_crash_after[scope_id] 可为 int（每次都崩）或 list（按 attempt 序：[0,0] 前两次崩、之后成功）
        nc = self.network_crash_after.get(job.scope_id)
        net_crash_at = nc[attempt] if isinstance(nc, list) and attempt < len(nc) else (nc if isinstance(nc, int) else None)
        i = 0
        for ev in events:
            if handle.stopped:  # 被 schedule 优雅停 → worker 配合退出（ADR 0024 终止契约），收尾事件另由 tail_after_stop 给
                yield from self._tail(job)
                self._maybe_exit(job)
                return
            if net_crash_at is not None and i >= net_crash_at:
                raise WorkerNetworkError(f"fake worker {job.scope_id} 建连失败（attempt {attempt}）")
            if crash_at is not None and i >= crash_at:
                raise RuntimeError(f"fake worker {job.scope_id} 在第 {i} 个事件后崩溃")
            if self.on_event is not None:
                self.on_event(job.scope_id, i)
            yield ev
            i += 1
        # 事件流走完后若仍要 network-crash（net_crash_at 不小于事件数，模拟「零/少事件就建连失败」）
        if net_crash_at is not None and i >= net_crash_at:
            raise WorkerNetworkError(f"fake worker {job.scope_id} 建连失败（attempt {attempt}）")
        if crash_at is not None and i >= crash_at:  # 同理：crash_after 等于事件数即「发完全部事件后崩」（退出码未知）
            raise RuntimeError(f"fake worker {job.scope_id} 在第 {i} 个事件后崩溃")
        if job.scope_id in self.tail_after_stop or job.scope_id in self.hang_after_stop:
            # 真 worker 发完事件后仍活着、等被停（这里的事件由后台 reader 线程抢先读完，不等就会在 stop 到达前 EOF）；
            # 等到停止请求再发收尾事件（模拟 SIGTERM 后的终结四阶段）。等不到即按 EOF 结束（测试不配 stop 时不挂死）。
            handle.wait_stopped(5.0)
            if handle.stopped:
                yield from self._tail(job)
        self._maybe_exit(job)

    def _tail(self, job: Job) -> Iterator[Event]:
        if job.scope_id in self.hang_after_stop:
            threading.Event().wait()  # 永不返回：reader 线程是 daemon，不挡测试进程退出
        if self.tail_delay_s:
            import time
            time.sleep(self.tail_delay_s)
        yield from self.tail_after_stop.get(job.scope_id, [])

    def _maybe_exit(self, job: Job) -> None:
        rc = self.exit_code.get(job.scope_id)
        if rc:
            raise WorkerExitError(rc, f"fake worker {job.scope_id} 异常退出 returncode={rc}")


class CollectSink:
    """收集所有事件（按到达序）的 sink，供断言。线程安全由 schedule 的 sink_lock 保证。"""

    def __init__(self) -> None:
        self.events: list[Event] = []

    def __call__(self, event: Event) -> None:
        self.events.append(event)


class FakeResolver:
    """EngineResolver：所有引擎都返回同一个 FakeEngine（测试不区分引擎）。"""

    def __init__(self, engine: FakeEngine) -> None:
        self.engine = engine

    def __call__(self, engine_name: str) -> FakeEngine:
        return self.engine
