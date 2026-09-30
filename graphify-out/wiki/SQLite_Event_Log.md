# SQLite Event Log

> 19 nodes · cohesion 0.15

## Key Concepts

- **SqliteEventLog** (27 connections) — `core/gherkai_core/adapters/event_log/sqlite.py`
- **._connect()** (8 connections) — `core/gherkai_core/adapters/event_log/sqlite.py`
- **.records()** (6 connections) — `core/gherkai_core/adapters/event_log/sqlite.py`
- **.append_event()** (3 connections) — `core/gherkai_core/adapters/event_log/sqlite.py`
- **.has_exit()** (3 connections) — `core/gherkai_core/adapters/event_log/sqlite.py`
- **.__init__()** (3 connections) — `core/gherkai_core/adapters/event_log/sqlite.py`
- **._init_schema()** (3 connections) — `core/gherkai_core/adapters/event_log/sqlite.py`
- **.max_seq()** (3 connections) — `core/gherkai_core/adapters/event_log/sqlite.py`
- **.record_exit()** (3 connections) — `core/gherkai_core/adapters/event_log/sqlite.py`
- **test_opening_a_v140_shaped_db_adds_the_reason_column()** (3 connections) — `core/tests/test_sqlite_event_log.py`
- **Connection** (1 connections)
- **Path** (1 connections)
- **某 scope 当前 events 的 max seq（per-run 进程读 fd3 时续号用；空 → 0）。** (1 connections) — `core/gherkai_core/adapters/event_log/sqlite.py`
- **本机 SQLite 事件日志（组合根注入路径；per-run 进程写、reconciler 读）。** (1 connections) — `core/gherkai_core/adapters/event_log/sqlite.py`
- **追加一条 worker 事件（原始 JSON 行）。INSERT OR REPLACE：同 (scope,seq) 幂等（重放/重试无副作用）。** (1 connections) — `core/gherkai_core/adapters/event_log/sqlite.py`
- **写平台侧退出记录（per-run 进程 proc.wait() 拿到 exitcode 后调，机制二）。INSERT OR REPLACE 幂等。…** (1 connections) — `core/gherkai_core/adapters/event_log/sqlite.py`
- **单个 scope 有没有退出记录（**只读**，exits 主键点查）——对位 `DdbEventLog.has_exit`，两侧结构相同。** (1 connections) — `core/gherkai_core/adapters/event_log/sqlite.py`
- **读回全量 records（供 project() 全量重放）：worker 事件（解析回 Event）+ 退出记录。 events 行的原始 JSON 用…** (1 connections) — `core/gherkai_core/adapters/event_log/sqlite.py`
- **唯一存活的迁移分支必须有红灯：v1.4.0（已发行）建的 exits 表没有 reason 列，新版接力同一 run 的 events.db 时…** (1 connections) — `core/tests/test_sqlite_event_log.py`

## Relationships

- [Event Log Adapters](Event_Log_Adapters.md) (6 shared connections)
- [Reconciler Orchestration](Reconciler_Orchestration.md) (3 shared connections)
- [SQLite Event Log](SQLite_Event_Log.md) (3 shared connections)
- [Local Reconcile Loop Tests](Local_Reconcile_Loop_Tests.md) (2 shared connections)
- [Wall Clock Timestamps](Wall_Clock_Timestamps.md) (2 shared connections)
- [Local Detached Execution](Local_Detached_Execution.md) (1 shared connections)
- [Local Subprocess Launcher](Local_Subprocess_Launcher.md) (1 shared connections)
- [CLI Command Handlers](CLI_Command_Handlers.md) (1 shared connections)
- [Job Domain Models](Job_Domain_Models.md) (1 shared connections)
- [Typed Errors and Wire Protocol](Typed_Errors_and_Wire_Protocol.md) (1 shared connections)

## Source Files

- `core/gherkai_core/adapters/event_log/sqlite.py`
- `core/tests/test_sqlite_event_log.py`

## Audit Trail

- EXTRACTED: 39 (85%)
- INFERRED: 7 (15%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*