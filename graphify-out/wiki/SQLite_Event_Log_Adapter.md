# SQLite Event Log Adapter

> 106 nodes · cohesion 0.04

## Key Concepts

- **LocalRunStore** (53 connections) — `core/gherkai_core/adapters/run_store/local.py`
- **test_detached_launcher.py** (32 connections) — `runtime/tests/test_detached_launcher.py`
- **SqliteEventLog** (27 connections) — `core/gherkai_core/adapters/event_log/sqlite.py`
- **run_store/local.py** (24 connections) — `core/gherkai_core/adapters/run_store/local.py`
- **subprocess_engine.py** (23 connections) — `core/gherkai_core/adapters/subprocess_engine.py`
- **SubprocessEngine** (21 connections) — `core/gherkai_core/adapters/subprocess_engine.py`
- **detached.py** (20 connections) — `runtime/gherkai_runtime/detached.py`
- **build_local_reconcile()** (20 connections) — `runtime/gherkai_runtime/detached.py`
- **run_reconcile_loop()** (20 connections) — `runtime/gherkai_runtime/detached.py`
- **SubprocessLauncher** (17 connections) — `runtime/gherkai_runtime/detached.py`
- **_setup()** (15 connections) — `runtime/tests/test_detached_launcher.py`
- **_seed_for_build()** (13 connections) — `runtime/tests/test_detached_launcher.py`
- **test_report_still_written_when_the_run_duration_read_fails()** (13 connections) — `runtime/tests/test_detached_launcher.py`
- **test_run_state_timestamps_share_one_format()** (13 connections) — `runtime/tests/test_detached_launcher.py`
- **event_log/__init__.py** (11 connections) — `core/gherkai_core/adapters/event_log/__init__.py`
- **_job()** (10 connections) — `runtime/tests/test_detached_launcher.py`
- **test_local_run_store_atomic.py** (9 connections) — `core/tests/test_local_run_store_atomic.py`
- **._connect()** (8 connections) — `core/gherkai_core/adapters/event_log/sqlite.py`
- **test_build_local_reconcile_reads_steps_dir_from_definition()** (8 connections) — `runtime/tests/test_detached_launcher.py`
- **test_build_local_reconcile_resolves_region_like_foreground()** (8 connections) — `runtime/tests/test_detached_launcher.py`
- **._locked_rmw()** (7 connections) — `core/gherkai_core/adapters/run_store/local.py`
- **_echo_resolver()** (7 connections) — `runtime/tests/test_detached_launcher.py`
- **test_grace_query_failure_never_spawns_a_worker()** (7 connections) — `runtime/tests/test_detached_launcher.py`
- **drive_local_reconcile()** (6 connections) — `runtime/gherkai_runtime/detached.py`
- **_now()** (6 connections) — `runtime/tests/test_detached_launcher.py`
- *... and 81 more nodes in this community*

## Relationships

- [Cloud Launcher & Fargate Adapters](Cloud_Launcher_%26_Fargate_Adapters.md) (32 shared connections)
- [Run State Rendering & DDB Store](Run_State_Rendering_%26_DDB_Store.md) (25 shared connections)
- [Job State Serialization](Job_State_Serialization.md) (23 shared connections)
- [Job/Scenario Explain Model](Job-Scenario_Explain_Model.md) (10 shared connections)
- [Reconcile Tick & Report Finalize](Reconcile_Tick_%26_Report_Finalize.md) (9 shared connections)
- [Cloud Store Composition Root](Cloud_Store_Composition_Root.md) (9 shared connections)
- [Fake DDB Table & SQLite Records](Fake_DDB_Table_%26_SQLite_Records.md) (7 shared connections)
- [Local Result Store & Persistence](Local_Result_Store_%26_Persistence.md) (7 shared connections)
- [Subprocess Engine Logging](Subprocess_Engine_Logging.md) (6 shared connections)
- [SQLite Event Log](SQLite_Event_Log.md) (4 shared connections)
- [Lambda Handler Event Parsing Tests](Lambda_Handler_Event_Parsing_Tests.md) (4 shared connections)
- [Subprocess Worker Handle](Subprocess_Worker_Handle.md) (4 shared connections)

## Source Files

- `core/gherkai_core/adapters/event_log/__init__.py`
- `core/gherkai_core/adapters/event_log/sqlite.py`
- `core/gherkai_core/adapters/run_store/__init__.py`
- `core/gherkai_core/adapters/run_store/local.py`
- `core/gherkai_core/adapters/subprocess_engine.py`
- `core/tests/test_local_run_store_atomic.py`
- `runtime/gherkai_runtime/compose.py`
- `runtime/gherkai_runtime/detached.py`
- `runtime/tests/test_detached_launcher.py`

## Audit Trail

- EXTRACTED: 332 (91%)
- INFERRED: 34 (9%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*