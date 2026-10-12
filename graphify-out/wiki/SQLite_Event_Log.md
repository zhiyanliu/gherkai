# SQLite Event Log

> 15 nodes · cohesion 0.19

## Key Concepts

- **SqliteEventLog** (27 connections) — `core/gherkai_core/adapters/event_log/sqlite.py`
- **._connect()** (8 connections) — `core/gherkai_core/adapters/event_log/sqlite.py`
- **.append_event()** (3 connections) — `core/gherkai_core/adapters/event_log/sqlite.py`
- **.has_exit()** (3 connections) — `core/gherkai_core/adapters/event_log/sqlite.py`
- **.__init__()** (3 connections) — `core/gherkai_core/adapters/event_log/sqlite.py`
- **._init_schema()** (3 connections) — `core/gherkai_core/adapters/event_log/sqlite.py`
- **.max_seq()** (3 connections) — `core/gherkai_core/adapters/event_log/sqlite.py`
- **.record_exit()** (3 connections) — `core/gherkai_core/adapters/event_log/sqlite.py`
- **Connection** (1 connections)
- **Path** (1 connections)
- **某 scope 当前 events 的 max seq（per-run 进程读 fd3 时续号用；空 → 0）。** (1 connections) — `core/gherkai_core/adapters/event_log/sqlite.py`
- **本机 SQLite 事件日志（组合根注入路径；per-run 进程写、reconciler 读）。** (1 connections) — `core/gherkai_core/adapters/event_log/sqlite.py`
- **追加一条 worker 事件（原始 JSON 行）。INSERT OR REPLACE：同 (scope,seq) 幂等（重放/重试无副作用）。** (1 connections) — `core/gherkai_core/adapters/event_log/sqlite.py`
- **写平台侧退出记录（per-run 进程 proc.wait() 拿到 exitcode 后调，机制二）。INSERT OR REPLACE 幂等。…** (1 connections) — `core/gherkai_core/adapters/event_log/sqlite.py`
- **单个 scope 有没有退出记录（**只读**，exits 主键点查）——对位 `DdbEventLog.has_exit`，两侧结构相同。** (1 connections) — `core/gherkai_core/adapters/event_log/sqlite.py`

## Relationships

- [EventLog And Launcher Ports](EventLog_And_Launcher_Ports.md) (3 shared connections)
- [SQLite Event Log Tests](SQLite_Event_Log_Tests.md) (3 shared connections)
- [Detached Launcher Reconcile Loop](Detached_Launcher_Reconcile_Loop.md) (2 shared connections)
- [Cloud Adapter Boundary Modules](Cloud_Adapter_Boundary_Modules.md) (2 shared connections)
- [Event Wire Protocol](Event_Wire_Protocol.md) (2 shared connections)
- [Timestamp & Wallclock Utils](Timestamp_%26_Wallclock_Utils.md) (2 shared connections)
- [Local Reconcile Rebuild](Local_Reconcile_Rebuild.md) (1 shared connections)
- [Detached Local Run Host](Detached_Local_Run_Host.md) (1 shared connections)
- [Subprocess Engine & Launcher](Subprocess_Engine_%26_Launcher.md) (1 shared connections)
- [Reconciler Event Projection](Reconciler_Event_Projection.md) (1 shared connections)
- [CLI Command Entry Points](CLI_Command_Entry_Points.md) (1 shared connections)
- [Lambda Handler Event Parsing Tests](Lambda_Handler_Event_Parsing_Tests.md) (1 shared connections)

## Source Files

- `core/gherkai_core/adapters/event_log/sqlite.py`

## Audit Trail

- EXTRACTED: 33 (82%)
- INFERRED: 7 (18%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*