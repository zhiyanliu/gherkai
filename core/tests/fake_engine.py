"""内存假 Engine（测试夹具，ADR 0026「接口是测试面」）。

直接在进程内吐预设的 ADR 0024 事件流，不 spawn 子进程、不连 AgentCore。
支持：正常事件流、worker 崩（迭代中抛异常）、慢 worker（配合 fake clock 测超时）、记录 stop。
"""
from __future__ import annotations

import threading
from typing import Callable, Iterator

from gherkai_core.errors import WorkerNetworkError
from gherkai_core.model import Event, Job


class FakeWorkerHandle:
    def __init__(self) -> None:
        self.stopped = False
        self.stop_grace: float | None = None

    def stop(self, grace_period_s: float) -> None:
        self.stopped = True
        self.stop_grace = grace_period_s


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
    ) -> None:
        self.behaviors = behaviors
        self.crash_after = crash_after or {}
        # network_crash_after: scope_id -> 第 N 个事件后抛 WorkerNetworkError（模拟建连失败，ADR 0028）。
        # N=0 模拟「会话未起就建连失败」（零事件）。每个 scope_id 的崩溃次数可用 list 表达递减（模拟重试后成功）。
        self.network_crash_after = network_crash_after or {}
        self.run_count: dict[str, int] = {}  # 每个 scope_id 被 run_scope 的次数（验证 job 级重试）
        self.on_event = on_event
        self.handles: dict[str, FakeWorkerHandle] = {}
        self._lock = threading.Lock()

    def run_scope(self, job: Job) -> tuple[FakeWorkerHandle, Iterator[Event]]:
        handle = FakeWorkerHandle()
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
            if handle.stopped:  # 被 schedule 优雅停 → worker 配合退出（ADR 0024 终止契约）
                return
            if net_crash_at is not None and i >= net_crash_at:
                raise WorkerNetworkError(f"fake worker {job.scope_id} 建连失败（attempt {attempt}）")
            if crash_at is not None and i >= crash_at:
                raise RuntimeError(f"fake worker {job.scope_id} 在第 {i} 个事件后崩溃")
            if self.on_event is not None:
                self.on_event(job.scope_id, i)
            yield ev
            i += 1
        # 事件流跑完后若仍要 network-crash（net_crash_at >= 事件数，模拟「零/少事件就建连失败」）
        if net_crash_at is not None and i >= net_crash_at:
            raise WorkerNetworkError(f"fake worker {job.scope_id} 建连失败（attempt {attempt}）")


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
