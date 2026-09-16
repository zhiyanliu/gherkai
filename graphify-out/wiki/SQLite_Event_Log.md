# SQLite Event Log

> 82 nodes · cohesion 0.04

## Key Concepts

- **test_detached_launcher.py** (30 connections) — `runtime/tests/test_detached_launcher.py`
- **SqliteEventLog** (27 connections) — `core/gherkai_core/adapters/event_log/sqlite.py`
- **SubprocessEngine** (21 connections) — `core/gherkai_core/adapters/subprocess_engine.py`
- **detached.py** (19 connections) — `runtime/gherkai_runtime/detached.py`
- **build_local_reconcile()** (19 connections) — `runtime/gherkai_runtime/detached.py`
- **run_reconcile_loop()** (19 connections) — `runtime/gherkai_runtime/detached.py`
- **subprocess_engine.py** (16 connections) — `core/gherkai_core/adapters/subprocess_engine.py`
- **SubprocessLauncher** (16 connections) — `runtime/gherkai_runtime/detached.py`
- **_setup()** (14 connections) — `runtime/tests/test_detached_launcher.py`
- **test_report_still_written_when_the_run_duration_read_fails()** (13 connections) — `runtime/tests/test_detached_launcher.py`
- **test_run_state_timestamps_share_one_format()** (13 connections) — `runtime/tests/test_detached_launcher.py`
- **_seed_for_build()** (12 connections) — `runtime/tests/test_detached_launcher.py`
- **_job()** (10 connections) — `runtime/tests/test_detached_launcher.py`
- **._connect()** (8 connections) — `core/gherkai_core/adapters/event_log/sqlite.py`
- **test_build_local_reconcile_reads_steps_dir_from_definition()** (8 connections) — `runtime/tests/test_detached_launcher.py`
- **test_build_local_reconcile_resolves_region_like_foreground()** (8 connections) — `runtime/tests/test_detached_launcher.py`
- **drive_local_reconcile()** (6 connections) — `runtime/gherkai_runtime/detached.py`
- **_echo_resolver()** (6 connections) — `runtime/tests/test_detached_launcher.py`
- **test_drive_local_reconcile_drives_to_terminal_then_tears_down_tunnel()** (6 connections) — `runtime/tests/test_detached_launcher.py`
- **test_job_timeout_stops_worker_and_attributes_timeout()** (6 connections) — `runtime/tests/test_detached_launcher.py`
- **_now()** (5 connections) — `runtime/tests/test_detached_launcher.py`
- **test_crash_worker_finalizes_error()** (5 connections) — `runtime/tests/test_detached_launcher.py`
- **test_single_job_passes_end_to_end()** (5 connections) — `runtime/tests/test_detached_launcher.py`
- **test_two_jobs_concurrency_one()** (5 connections) — `runtime/tests/test_detached_launcher.py`
- **now_iso()** (4 connections) — `runtime/gherkai_runtime/compose.py`
- *... and 57 more nodes in this community*

## Relationships

- [DynamoDB RunStore Adapter](DynamoDB_RunStore_Adapter.md) (17 shared connections)
- [Job Explain & S3 Offload](Job_Explain_%26_S3_Offload.md) (16 shared connections)
- [Cloud Boto3 Guards & EventLog](Cloud_Boto3_Guards_%26_EventLog.md) (11 shared connections)
- [Runtime Composition Root](Runtime_Composition_Root.md) (9 shared connections)
- [S3 Report Store & Control Plane](S3_Report_Store_%26_Control_Plane.md) (6 shared connections)
- [Run State Rendering](Run_State_Rendering.md) (6 shared connections)
- [Reconciler Ports](Reconciler_Ports.md) (5 shared connections)
- [Worker Process Handle & Event Pump](Worker_Process_Handle_%26_Event_Pump.md) (5 shared connections)
- [Subprocess Engine Tests](Subprocess_Engine_Tests.md) (4 shared connections)
- [SQLite Event Log Tests](SQLite_Event_Log_Tests.md) (3 shared connections)
- [Cloud Job Launcher](Cloud_Job_Launcher.md) (3 shared connections)
- [Run State Projection](Run_State_Projection.md) (3 shared connections)

## Source Files

- `core/gherkai_core/adapters/event_log/sqlite.py`
- `core/gherkai_core/adapters/subprocess_engine.py`
- `runtime/gherkai_runtime/compose.py`
- `runtime/gherkai_runtime/detached.py`
- `runtime/tests/test_detached_launcher.py`

## Audit Trail

- EXTRACTED: 224 (89%)
- INFERRED: 27 (11%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*