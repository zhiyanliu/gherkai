# Cloud Launcher & DDB Event Log

> 48 nodes · cohesion 0.08

## Key Concepts

- **test_cloud_reconcile.py** (36 connections) — `core/tests/test_cloud_reconcile.py`
- **DdbEventLog** (21 connections) — `core/gherkai_core/adapters/event_log/ddb.py`
- **CloudLauncher** (17 connections) — `core/gherkai_core/adapters/cloud_launcher.py`
- **_RecorderWatch** (15 connections) — `core/tests/test_cloud_reconcile.py`
- **_FakeStartEngine** (14 connections) — `core/tests/test_cloud_reconcile.py`
- **_job()** (11 connections) — `core/tests/test_cloud_reconcile.py`
- **test_tick_with_ddb_backend()** (10 connections) — `core/tests/test_cloud_reconcile.py`
- **_passed_worker_events()** (8 connections) — `core/tests/test_cloud_reconcile.py`
- **_meta()** (6 connections) — `core/tests/test_cloud_reconcile.py`
- **test_cloud_launcher_arm_failure_does_not_block_launch()** (6 connections) — `core/tests/test_cloud_reconcile.py`
- **test_cloud_launcher_arms_timeout_watch()** (6 connections) — `core/tests/test_cloud_reconcile.py`
- **test_cloud_launcher_no_arm_without_timeout()** (6 connections) — `core/tests/test_cloud_reconcile.py`
- **test_ddb_multi_scope_records()** (6 connections) — `core/tests/test_cloud_reconcile.py`
- **test_ddb_records_feed_project()** (6 connections) — `core/tests/test_cloud_reconcile.py`
- **test_cloud_launcher_calls_start_scope()** (5 connections) — `core/tests/test_cloud_reconcile.py`
- **test_cloud_launcher_launch_failure_still_armed_and_raises()** (5 connections) — `core/tests/test_cloud_reconcile.py`
- **test_ddb_record_exit_independent_keyspace()** (5 connections) — `core/tests/test_cloud_reconcile.py`
- **_put_worker_event()** (4 connections) — `core/tests/test_cloud_reconcile.py`
- **test_cloud_launcher_arms_before_start_scope()** (4 connections) — `core/tests/test_cloud_reconcile.py`
- **test_ddb_has_exit_single_scope()** (4 connections) — `core/tests/test_cloud_reconcile.py`
- **._emit_ts()** (3 connections) — `core/gherkai_core/adapters/event_log/ddb.py`
- **events_table()** (3 connections) — `core/tests/test_cloud_reconcile.py`
- **test_ddb_event_log_reads_worker_events()** (3 connections) — `core/tests/test_cloud_reconcile.py`
- **.launch()** (2 connections) — `core/gherkai_core/adapters/cloud_launcher.py`
- **.__init__()** (1 connections) — `core/gherkai_core/adapters/cloud_launcher.py`
- *... and 23 more nodes in this community*

## Relationships

- [Engine Ports & Adapters](Engine_Ports_%26_Adapters.md) (16 shared connections)
- [Run Result Rendering](Run_Result_Rendering.md) (10 shared connections)
- [Run State Rendering](Run_State_Rendering.md) (8 shared connections)
- [Task Exit Event Records](Task_Exit_Event_Records.md) (5 shared connections)
- [SQLite Event Log](SQLite_Event_Log.md) (4 shared connections)
- [Boto Guard & S3 Offload](Boto_Guard_%26_S3_Offload.md) (4 shared connections)
- [Reconciler Lambda](Reconciler_Lambda.md) (3 shared connections)
- [Event Replay Projection](Event_Replay_Projection.md) (3 shared connections)
- [Fargate Engine Tests](Fargate_Engine_Tests.md) (2 shared connections)
- [Run Scheduling Engine](Run_Scheduling_Engine.md) (2 shared connections)
- [Exit Observer Lambda](Exit_Observer_Lambda.md) (1 shared connections)

## Source Files

- `core/gherkai_core/adapters/cloud_launcher.py`
- `core/gherkai_core/adapters/event_log/ddb.py`
- `core/tests/test_cloud_reconcile.py`

## Audit Trail

- EXTRACTED: 119 (83%)
- INFERRED: 25 (17%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*