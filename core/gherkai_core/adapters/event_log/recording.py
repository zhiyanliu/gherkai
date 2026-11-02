"""把 SubprocessEngine 的原始事件行旁路落 SqliteEventLog（ADR 0042 决策七、ADR 0034）。

两处用同一份写法：无状态批量运行的 SubprocessLauncher（launch 时直接传 raw_sink），以及本机同步 `run`（组合根给引擎包一层
EventRecordingEngine，Engine port 形状不变、schedule 不知情）。存原始行、读回复用 wire.event_from_line，零新序列化；seq 按到达序
在该 scope 内单调递增，从库里已有的 max_seq 续号（同一 scope 重试或继续运行时幂等）；emit_ts 取到达时刻。
"""
from __future__ import annotations

import time
from collections.abc import Callable, Iterator

from gherkai_core.adapters.event_log.sqlite import SqliteEventLog
from gherkai_core.adapters.subprocess_engine import SubprocessEngine
from gherkai_core.model import Event, Job
from gherkai_core.ports import WorkerHandle


def make_raw_sink(event_log: SqliteEventLog, scope_id: str) -> Callable[[str], None]:
    """一个 scope 的原始事件行落库回调。闭包持 seq，读 fd3 的线程内单线程递增、无竞态。"""
    seq_box = [event_log.max_seq(scope_id)]

    def raw_sink(line: str) -> None:
        seq_box[0] += 1
        event_log.append_event(scope_id, seq_box[0], line, time.time())

    return raw_sink


class EventRecordingEngine:
    """给 SubprocessEngine 包一层：run_scope 时把该 job 的原始事件行落 SqliteEventLog，其余原样转发。

    只包 SubprocessEngine（raw_sink 是它的扩展形参、不在 Engine port 契约里）；定位失败的占位引擎不包，让它的安装指引
    照常在 run_scope 时抛出。
    """

    def __init__(self, inner: SubprocessEngine, event_log: SqliteEventLog) -> None:
        self._inner = inner
        self._event_log = event_log

    def run_scope(self, job: Job) -> tuple[WorkerHandle, Iterator[Event]]:
        return self._inner.run_scope(job, raw_sink=make_raw_sink(self._event_log, job.scope_id))

    def __getattr__(self, name: str):  # 其余成员（如能力自述）原样转发
        return getattr(self._inner, name)
