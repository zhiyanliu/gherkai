# SQLite Event Log

> 34 nodes · cohesion 0.09

## Key Concepts

- **SqliteEventLog** (27 connections) — `core/gherkai_core/adapters/event_log/sqlite.py`
- **test_sqlite_event_log.py** (21 connections) — `core/tests/test_sqlite_event_log.py`
- **_log()** (10 connections) — `core/tests/test_sqlite_event_log.py`
- **._connect()** (8 connections) — `core/gherkai_core/adapters/event_log/sqlite.py`
- **.records()** (6 connections) — `core/gherkai_core/adapters/event_log/sqlite.py`
- **.append_event()** (3 connections) — `core/gherkai_core/adapters/event_log/sqlite.py`
- **.has_exit()** (3 connections) — `core/gherkai_core/adapters/event_log/sqlite.py`
- **.__init__()** (3 connections) — `core/gherkai_core/adapters/event_log/sqlite.py`
- **._init_schema()** (3 connections) — `core/gherkai_core/adapters/event_log/sqlite.py`
- **.max_seq()** (3 connections) — `core/gherkai_core/adapters/event_log/sqlite.py`
- **.record_exit()** (3 connections) — `core/gherkai_core/adapters/event_log/sqlite.py`
- **test_append_idempotent_same_seq()** (3 connections) — `core/tests/test_sqlite_event_log.py`
- **test_exit_code_none_stored()** (3 connections) — `core/tests/test_sqlite_event_log.py`
- **test_exit_record_independent_keyspace()** (3 connections) — `core/tests/test_sqlite_event_log.py`
- **test_has_exit_single_scope()** (3 connections) — `core/tests/test_sqlite_event_log.py`
- **test_opening_a_v140_shaped_db_adds_the_reason_column()** (3 connections) — `core/tests/test_sqlite_event_log.py`
- **test_record_exit_reason_roundtrip()** (3 connections) — `core/tests/test_sqlite_event_log.py`
- **test_append_and_read_back_events()** (2 connections) — `core/tests/test_sqlite_event_log.py`
- **test_max_seq_empty_is_zero()** (2 connections) — `core/tests/test_sqlite_event_log.py`
- **Connection** (1 connections)
- **Path** (1 connections)
- **某 scope 当前 events 的 max seq（per-run 进程读 fd3 时续号用；空 → 0）。** (1 connections) — `core/gherkai_core/adapters/event_log/sqlite.py`
- **本机 SQLite 事件日志（组合根注入路径；per-run 进程写、reconciler 读）。** (1 connections) — `core/gherkai_core/adapters/event_log/sqlite.py`
- **追加一条 worker 事件（原始 JSON 行）。INSERT OR REPLACE：同 (scope,seq) 幂等（重放/重试无副作用）。** (1 connections) — `core/gherkai_core/adapters/event_log/sqlite.py`
- **写平台侧退出记录（per-run 进程 proc.wait() 拿到 exitcode 后调，机制二）。INSERT OR REPLACE 幂等。…** (1 connections) — `core/gherkai_core/adapters/event_log/sqlite.py`
- *... and 9 more nodes in this community*

## Relationships

- [Event Log & Projection](Event_Log_%26_Projection.md) (7 shared connections)
- [Run Metadata & S3 Offload](Run_Metadata_%26_S3_Offload.md) (7 shared connections)
- [Reconcile Orchestration](Reconcile_Orchestration.md) (3 shared connections)
- [DynamoDB Event Log](DynamoDB_Event_Log.md) (2 shared connections)
- [Detached Launcher Tests](Detached_Launcher_Tests.md) (2 shared connections)
- [Timestamps & Wallclock](Timestamps_%26_Wallclock.md) (2 shared connections)
- [Run State Rendering](Run_State_Rendering.md) (2 shared connections)
- [Local Reconcile Rebuild](Local_Reconcile_Rebuild.md) (1 shared connections)
- [Subprocess Engine Launcher](Subprocess_Engine_Launcher.md) (1 shared connections)
- [CLI Command Dispatch](CLI_Command_Dispatch.md) (1 shared connections)
- [Fargate Engine Adapter](Fargate_Engine_Adapter.md) (1 shared connections)

## Source Files

- `core/gherkai_core/adapters/event_log/sqlite.py`
- `core/tests/test_sqlite_event_log.py`

## Audit Trail

- EXTRACTED: 71 (91%)
- INFERRED: 7 (9%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*