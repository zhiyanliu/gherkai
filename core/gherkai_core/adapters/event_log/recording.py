"""把 SubprocessEngine 的原始事件行与退出记录旁路落 SqliteEventLog（ADR 0042 决策七、ADR 0034）。

两处用同一份写法：无状态批量运行的 SubprocessLauncher（launch 时直接传 raw_sink，退出记录由它的 _pump 写），以及本机同步 `run`
（组合根给引擎包一层 EventRecordingEngine，Engine port 形状不变、schedule 不知情）。存原始行、读回复用 wire.event_from_line，
零新序列化；seq 按到达序在该 scope 内单调递增，从库里已有的 max_seq 续号（同一 scope 重试或继续运行时幂等）；emit_ts 取到达时刻。

同步 run 的记录器也写**退出记录**（ADR 0034 机制二「两件都要」）：事件流自然结束或 worker 以非零退出码结束时按退出码写一条，被 schedule
主动停止（stop）时在停止完成后写——这样同步 run 的 events.db 与 detached 的形态相同（事件加退出记录），`status --wait` 的接力推进与
`explain` 的补取读到的是完整的事件流，不会把一个已结束的 job 当成仍在运行。
"""
from __future__ import annotations

import threading
import time
from collections.abc import Callable, Iterator

from gherkai_core.adapters.event_log.sqlite import SqliteEventLog
from gherkai_core.adapters.subprocess_engine import SubprocessEngine, SubprocessWorkerHandle
from gherkai_core.errors import WorkerExitError
from gherkai_core.model import Event, Job
from gherkai_core.ports import WorkerHandle


def make_raw_sink(event_log: SqliteEventLog, scope_id: str) -> Callable[[str], None]:
    """一个 scope 的原始事件行落库回调。闭包持 seq，读 fd3 的线程内单线程递增、无竞态。"""
    seq_box = [event_log.max_seq(scope_id)]

    def raw_sink(line: str) -> None:
        seq_box[0] += 1
        event_log.append_event(scope_id, seq_box[0], line, time.time())

    return raw_sink


class _ExitRecorder:
    """一个 job 的退出记录只写一次：事件迭代结束（含非零退出码的异常）或 stop 完成时，谁先到谁写。

    唯一的例外是用真码覆盖未知码：stop 的强杀分支先返回、退出码还没就位时按未知写了一条，随后 schedule 排空事件流读到带码的
    WorkerExitError——再写一次（INSERT OR REPLACE 同键），让记录与 launcher 经 wait 拿到的真码一致。

    两个调用方在不同线程（stop 由 schedule 的主线程调、事件迭代在该 scope 的读线程），判重与落库在同一把锁里串行：否则停止线程
    判完「未写过」、落库前被挂起，事件线程先写了真码，停止线程恢复后再把它覆盖成未知码（同僚复核用真实 SQLite 控制线程交错复现）。"""

    def __init__(self, event_log: SqliteEventLog, scope_id: str, handle: SubprocessWorkerHandle) -> None:
        self._event_log = event_log
        self._scope_id = scope_id
        self._handle = handle
        self._done = False
        self._recorded: int | None = None
        self._lock = threading.Lock()

    def record(self, exit_code: int | None) -> None:
        with self._lock:
            if self._done and (exit_code is None or self._recorded is not None):
                return
            self._done = True
            self._recorded = exit_code
            try:
                self._event_log.record_exit(self._scope_id, exit_code)
            except Exception:
                pass  # 落库失败不拖垮执行（与 raw_sink 同一口径）；判定真值走 RunPersistence，不依赖这条记录


class _RecordingHandle:
    """包住 worker 句柄：stop 完成后补写退出记录（schedule 主动停止时事件迭代器被放弃、不会自然结束）。其余成员原样转发。"""

    def __init__(self, inner: SubprocessWorkerHandle, recorder: _ExitRecorder) -> None:
        self._inner = inner
        self._recorder = recorder

    def stop(self, grace_period_s: float) -> None:
        try:
            self._inner.stop(grace_period_s)
        finally:
            self._recorder.record(self._exit_code_after_stop())

    _REAP_WAIT_S = 2.0  # stop 已向整组发过信号，进程只差被内核回收；SIGKILL 兜底与二次中断两条路径都是发出即返回、不等回收

    def _exit_code_after_stop(self) -> int | None:
        rc = self._inner.returncode()
        if rc is None:
            try:
                rc = self._inner.wait(self._REAP_WAIT_S)
            except Exception:
                rc = None  # 仍拿不到：按退出码未知写（投影判 ERROR、非宽限，ADR 0034 机制二「退出码缺失」条），与 launcher 同一口径
        return rc

    def __getattr__(self, name: str):
        return getattr(self._inner, name)


def _recording_events(events: Iterator[Event], recorder: _ExitRecorder, handle: SubprocessWorkerHandle) -> Iterator[Event]:
    try:
        yield from events
    except WorkerExitError as e:  # 非零退出码（含被信号强杀的负码）：按异常上的码记，再原样抛给 schedule
        recorder.record(e.exit_code)
        raise
    except GeneratorExit:  # schedule 停止后放弃迭代：退出记录由 stop 完成后写
        raise
    else:
        recorder.record(handle.returncode() if handle.returncode() is not None else 0)  # 自然 EOF：adapter 只在码为 0 时正常结束


class EventRecordingEngine:
    """给 SubprocessEngine 包一层：run_scope 时把该 job 的原始事件行与退出记录落 SqliteEventLog，其余原样转发。

    只包 SubprocessEngine（raw_sink 是它的扩展形参、不在 Engine port 契约里）；定位失败的占位引擎不包，让它的安装指引
    照常在 run_scope 时抛出。
    """

    def __init__(self, inner: SubprocessEngine, event_log: SqliteEventLog) -> None:
        self._inner = inner
        self._event_log = event_log

    def run_scope(self, job: Job) -> tuple[WorkerHandle, Iterator[Event]]:
        handle, events = self._inner.run_scope(job, raw_sink=make_raw_sink(self._event_log, job.scope_id))
        recorder = _ExitRecorder(self._event_log, job.scope_id, handle)
        return _RecordingHandle(handle, recorder), _recording_events(events, recorder, handle)

    def __getattr__(self, name: str):  # 其余成员（如能力自述）原样转发
        return getattr(self._inner, name)
