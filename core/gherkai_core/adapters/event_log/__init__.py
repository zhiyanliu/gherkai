"""events 日志 adapter（ADR 0034）：持久事件通道，reconciler 从此全量重放推演 RunState。

无状态批量运行的「写模型」持久层。云端后端下是 DDB events 表（worker PutItem，[0024]）；本机后端下是 SQLite（本模块）——
替易失的 FD3 pipe，使 CLI 脱离后 reconciler（per-run 进程 / status --wait 接力）仍能读回全量事件重放。
表结构镜像 DDB events 的单 PK 段：(scope_id, seq)（DDB 侧 PK=run_id#scope_id，本地库按 run 分文件、
run_id 隐含在路径里）+ 独立键空间的 task_exited 退出记录（机制一）。
"""
from gherkai_core.adapters.event_log.sqlite import SqliteEventLog
from gherkai_core.adapters.event_log.ddb import DdbEventLog

__all__ = ["SqliteEventLog", "DdbEventLog"]
