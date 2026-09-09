# SQLite Event Log

> 70 nodes · cohesion 0.05

## Key Concepts

- **test_reconcile.py** (29 connections) — `core/tests/test_reconcile.py`
- **SqliteEventLog** (24 connections) — `core/gherkai_core/adapters/event_log/sqlite.py`
- **tick()** (21 connections) — `core/gherkai_core/reconcile.py`
- **test_sqlite_event_log.py** (19 connections) — `core/tests/test_sqlite_event_log.py`
- **FakeLauncher** (16 connections) — `core/tests/test_reconcile.py`
- **_setup()** (14 connections) — `core/tests/test_reconcile.py`
- **BoomLauncher** (12 connections) — `core/tests/test_reconcile.py`
- **event_log/__init__.py** (11 connections) — `core/gherkai_core/adapters/event_log/__init__.py`
- **EventLog** (9 connections) — `core/gherkai_core/reconcile.py`
- **_log()** (9 connections) — `core/tests/test_sqlite_event_log.py`
- **._connect()** (8 connections) — `core/gherkai_core/adapters/event_log/sqlite.py`
- **Launcher** (8 connections) — `core/gherkai_core/reconcile.py`
- **_done_events()** (6 connections) — `core/tests/test_reconcile.py`
- **test_double_finalize_idempotent()** (6 connections) — `core/tests/test_reconcile.py`
- **test_tick_finalizes_when_all_done()** (6 connections) — `core/tests/test_reconcile.py`
- **test_tick_starts_next_after_completion()** (6 connections) — `core/tests/test_reconcile.py`
- **test_launch_failure_does_not_wedge_run()** (5 connections) — `core/tests/test_reconcile.py`
- **test_launch_failure_isolated_other_job_completes()** (5 connections) — `core/tests/test_reconcile.py`
- **test_tick_idempotent_no_double_launch()** (5 connections) — `core/tests/test_reconcile.py`
- **test_tick_nonzero_exit_finalizes_error()** (5 connections) — `core/tests/test_reconcile.py`
- **_meta()** (4 connections) — `core/tests/test_reconcile.py`
- **test_first_tick_starts_up_to_concurrency()** (4 connections) — `core/tests/test_reconcile.py`
- **.append_event()** (3 connections) — `core/gherkai_core/adapters/event_log/sqlite.py`
- **.has_exit()** (3 connections) — `core/gherkai_core/adapters/event_log/sqlite.py`
- **.__init__()** (3 connections) — `core/gherkai_core/adapters/event_log/sqlite.py`
- *... and 45 more nodes in this community*

## Relationships

- [Run Result Rendering](Run_Result_Rendering.md) (23 shared connections)
- [Engine Ports & Adapters](Engine_Ports_%26_Adapters.md) (23 shared connections)
- [Local Run Store](Local_Run_Store.md) (9 shared connections)
- [Run State Rendering](Run_State_Rendering.md) (9 shared connections)
- [Cloud Launcher & DDB Event Log](Cloud_Launcher_%26_DDB_Event_Log.md) (4 shared connections)
- [Boto Guard & S3 Offload](Boto_Guard_%26_S3_Offload.md) (4 shared connections)
- [Event Replay Projection](Event_Replay_Projection.md) (2 shared connections)
- [Lambda Handler Tests](Lambda_Handler_Tests.md) (1 shared connections)
- [S3 Report Store & Subprocess](S3_Report_Store_%26_Subprocess.md) (1 shared connections)
- [CLI Plan & Submit](CLI_Plan_%26_Submit.md) (1 shared connections)
- [State Projection & Planning](State_Projection_%26_Planning.md) (1 shared connections)
- [Reconciler Lambda](Reconciler_Lambda.md) (1 shared connections)

## Source Files

- `core/gherkai_core/adapters/event_log/__init__.py`
- `core/gherkai_core/adapters/event_log/sqlite.py`
- `core/gherkai_core/reconcile.py`
- `core/tests/test_reconcile.py`
- `core/tests/test_sqlite_event_log.py`

## Audit Trail

- EXTRACTED: 166 (86%)
- INFERRED: 27 (14%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*