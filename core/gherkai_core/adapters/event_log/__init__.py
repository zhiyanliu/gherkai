"""events 日志 adapter（ADR 0034）：持久事件通道，reconciler 从此全量重放推演 RunState。

无状态跑批的「写模型」持久层。cloud = DDB events 表（worker PutItem，[0024]）；local = SQLite（本模块）——
替易失的 FD3 pipe，使 CLI 脱离后 reconciler（per-run 进程 / status --wait 接力）仍能读回全量事件重放。
表结构镜像 DDB events：PK=scope_id / SK=seq（worker 段单调）+ 独立键空间的 task_exited 退出记录（机制一）。
"""
from gherkai_core.adapters.event_log.sqlite import SqliteEventLog
from gherkai_core.adapters.event_log.ddb import DdbEventLog

__all__ = ["SqliteEventLog", "DdbEventLog"]
