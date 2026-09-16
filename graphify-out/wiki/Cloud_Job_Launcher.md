# Cloud Job Launcher

> 59 nodes · cohesion 0.06

## Key Concepts

- **test_cloud_reconcile.py** (38 connections) — `core/tests/test_cloud_reconcile.py`
- **DdbEventLog** (25 connections) — `core/gherkai_core/adapters/event_log/ddb.py`
- **CloudLauncher** (17 connections) — `core/gherkai_core/adapters/cloud_launcher.py`
- **events_pk()** (15 connections) — `core/gherkai_core/adapters/fargate_engine.py`
- **_RecorderWatch** (15 connections) — `core/tests/test_cloud_reconcile.py`
- **_FakeStartEngine** (14 connections) — `core/tests/test_cloud_reconcile.py`
- **event_log/__init__.py** (11 connections) — `core/gherkai_core/adapters/event_log/__init__.py`
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
- **cloud_launcher.py** (4 connections) — `core/gherkai_core/adapters/cloud_launcher.py`
- **_put_worker_event()** (4 connections) — `core/tests/test_cloud_reconcile.py`
- **test_cloud_launcher_arms_before_start_scope()** (4 connections) — `core/tests/test_cloud_reconcile.py`
- **test_ddb_has_exit_single_scope()** (4 connections) — `core/tests/test_cloud_reconcile.py`
- **test_ddb_record_exit_reason_roundtrip()** (4 connections) — `core/tests/test_cloud_reconcile.py`
- **.has_exit()** (3 connections) — `core/gherkai_core/adapters/event_log/ddb.py`
- *... and 34 more nodes in this community*

## Relationships

- [Job Explain & S3 Offload](Job_Explain_%26_S3_Offload.md) (20 shared connections)
- [Cloud Boto3 Guards & EventLog](Cloud_Boto3_Guards_%26_EventLog.md) (12 shared connections)
- [Run State Projection](Run_State_Projection.md) (4 shared connections)
- [DynamoDB RunStore Adapter](DynamoDB_RunStore_Adapter.md) (4 shared connections)
- [Run State Rendering](Run_State_Rendering.md) (4 shared connections)
- [Reconciler Lambda](Reconciler_Lambda.md) (3 shared connections)
- [Fargate Engine Tests](Fargate_Engine_Tests.md) (3 shared connections)
- [Event Record Reading](Event_Record_Reading.md) (3 shared connections)
- [SQLite Event Log](SQLite_Event_Log.md) (3 shared connections)
- [Reconciler Ports](Reconciler_Ports.md) (3 shared connections)
- [Event Formatting](Event_Formatting.md) (2 shared connections)
- [Fargate Exit Code Tests](Fargate_Exit_Code_Tests.md) (2 shared connections)

## Source Files

- `core/gherkai_core/adapters/cloud_launcher.py`
- `core/gherkai_core/adapters/event_log/__init__.py`
- `core/gherkai_core/adapters/event_log/ddb.py`
- `core/gherkai_core/adapters/fargate_engine.py`
- `core/tests/test_cloud_reconcile.py`
- `core/tests/test_fargate_engine.py`

## Audit Trail

- EXTRACTED: 149 (85%)
- INFERRED: 27 (15%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*