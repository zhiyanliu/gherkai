# SQLite Event Log Store

> 17 nodes · cohesion 0.17

## Key Concepts

- **SqliteEventLog** (24 connections) — `core/gherkai_core/adapters/event_log/sqlite.py`
- **._connect()** (8 connections) — `core/gherkai_core/adapters/event_log/sqlite.py`
- **.records()** (6 connections) — `core/gherkai_core/adapters/event_log/sqlite.py`
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
- **单个 scope 有没有退出记录（**只读**，exits 主键点查）——对位 `DdbEventLog.has_exit`，两侧同形。** (1 connections) — `core/gherkai_core/adapters/event_log/sqlite.py`
- **读回全量 records（供 project() 全量重放）：worker 事件（解析回 Event）+ 退出记录。 events 行的原始 JSON 用…** (1 connections) — `core/gherkai_core/adapters/event_log/sqlite.py`

## Relationships

- [SQLite Event Log & Projection](SQLite_Event_Log_%26_Projection.md) (5 shared connections)
- [Reconcile Ports & Tick](Reconcile_Ports_%26_Tick.md) (2 shared connections)
- [SQLite Event Log Tests](SQLite_Event_Log_Tests.md) (2 shared connections)
- [Reconcile Loop Integration](Reconcile_Loop_Integration.md) (2 shared connections)
- [Engine Ports & Adapters](Engine_Ports_%26_Adapters.md) (2 shared connections)
- [Detached Launcher Reconcile](Detached_Launcher_Reconcile.md) (1 shared connections)
- [Cloud Launcher & DDB EventLog](Cloud_Launcher_%26_DDB_EventLog.md) (1 shared connections)
- [Subprocess Worker Launcher](Subprocess_Worker_Launcher.md) (1 shared connections)
- [CLI Run/Submit Commands](CLI_Run-Submit_Commands.md) (1 shared connections)
- [Timestamp and Clock Utilities](Timestamp_and_Clock_Utilities.md) (1 shared connections)

## Source Files

- `core/gherkai_core/adapters/event_log/sqlite.py`

## Audit Trail

- EXTRACTED: 35 (85%)
- INFERRED: 6 (15%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*