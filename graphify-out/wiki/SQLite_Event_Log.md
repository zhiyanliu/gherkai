# SQLite Event Log

> 19 nodes · cohesion 0.15

## Key Concepts

- **SqliteEventLog** (27 connections) — `core/gherkai_core/adapters/event_log/sqlite.py`
- **event_log/__init__.py** (11 connections) — `core/gherkai_core/adapters/event_log/__init__.py`
- **sqlite.py** (8 connections) — `core/gherkai_core/adapters/event_log/sqlite.py`
- **._connect()** (8 connections) — `core/gherkai_core/adapters/event_log/sqlite.py`
- **.append_event()** (3 connections) — `core/gherkai_core/adapters/event_log/sqlite.py`
- **.has_exit()** (3 connections) — `core/gherkai_core/adapters/event_log/sqlite.py`
- **.__init__()** (3 connections) — `core/gherkai_core/adapters/event_log/sqlite.py`
- **._init_schema()** (3 connections) — `core/gherkai_core/adapters/event_log/sqlite.py`
- **.max_seq()** (3 connections) — `core/gherkai_core/adapters/event_log/sqlite.py`
- **.record_exit()** (3 connections) — `core/gherkai_core/adapters/event_log/sqlite.py`
- **Connection** (1 connections)
- **events 日志 adapter（ADR 0034）：持久事件通道，reconciler 从此全量重放推演 RunState。…** (1 connections) — `core/gherkai_core/adapters/event_log/__init__.py`
- **Path** (1 connections)
- **SqliteEventLog（ADR 0034）：local 无状态批量运行的持久事件通道。 worker 事件（原始 ADR 0024 JSON 行 +…** (1 connections) — `core/gherkai_core/adapters/event_log/sqlite.py`
- **某 scope 当前 events 的 max seq（per-run 进程读 fd3 时续号用；空 → 0）。** (1 connections) — `core/gherkai_core/adapters/event_log/sqlite.py`
- **本机 SQLite 事件日志（组合根注入路径；per-run 进程写、reconciler 读）。** (1 connections) — `core/gherkai_core/adapters/event_log/sqlite.py`
- **追加一条 worker 事件（原始 JSON 行）。INSERT OR REPLACE：同 (scope,seq) 幂等（重放/重试无副作用）。** (1 connections) — `core/gherkai_core/adapters/event_log/sqlite.py`
- **写平台侧退出记录（per-run 进程 proc.wait() 拿到 exitcode 后调，机制二）。INSERT OR REPLACE 幂等。…** (1 connections) — `core/gherkai_core/adapters/event_log/sqlite.py`
- **单个 scope 有没有退出记录（**只读**，exits 主键点查）——对位 `DdbEventLog.has_exit`，两侧结构相同。** (1 connections) — `core/gherkai_core/adapters/event_log/sqlite.py`

## Relationships

- [Event Records Projection](Event_Records_Projection.md) (6 shared connections)
- [Reconcile Tick and Report](Reconcile_Tick_and_Report.md) (4 shared connections)
- [SQLite Event Log Tests](SQLite_Event_Log_Tests.md) (4 shared connections)
- [Detached Reconcile Loop Tests](Detached_Reconcile_Loop_Tests.md) (3 shared connections)
- [Cloud Launcher and EventLog](Cloud_Launcher_and_EventLog.md) (2 shared connections)
- [Lambda Handler Event Tests](Lambda_Handler_Event_Tests.md) (2 shared connections)
- [Event Wire Serialization](Event_Wire_Serialization.md) (2 shared connections)
- [Wallclock Timestamp Source](Wallclock_Timestamp_Source.md) (2 shared connections)
- [Boto3 Adapter Guard](Boto3_Adapter_Guard.md) (1 shared connections)
- [Local Detached Reconcile](Local_Detached_Reconcile.md) (1 shared connections)
- [Result Tree Text Rendering](Result_Tree_Text_Rendering.md) (1 shared connections)
- [Local Reconcile Rebuild](Local_Reconcile_Rebuild.md) (1 shared connections)

## Source Files

- `core/gherkai_core/adapters/event_log/__init__.py`
- `core/gherkai_core/adapters/event_log/sqlite.py`

## Audit Trail

- EXTRACTED: 49 (88%)
- INFERRED: 7 (12%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*