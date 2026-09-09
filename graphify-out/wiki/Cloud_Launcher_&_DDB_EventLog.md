# Cloud Launcher & DDB EventLog

> 61 nodes · cohesion 0.06

## Key Concepts

- **test_cloud_reconcile.py** (36 connections) — `core/tests/test_cloud_reconcile.py`
- **DdbEventLog** (21 connections) — `core/gherkai_core/adapters/event_log/ddb.py`
- **CloudLauncher** (17 connections) — `core/gherkai_core/adapters/cloud_launcher.py`
- **_RecorderWatch** (15 connections) — `core/tests/test_cloud_reconcile.py`
- **events_pk()** (14 connections) — `core/gherkai_core/adapters/fargate_engine.py`
- **_FakeStartEngine** (14 connections) — `core/tests/test_cloud_reconcile.py`
- **event_log/ddb.py** (12 connections) — `core/gherkai_core/adapters/event_log/ddb.py`
- **event_log/__init__.py** (11 connections) — `core/gherkai_core/adapters/event_log/__init__.py`
- **_job()** (11 connections) — `core/tests/test_cloud_reconcile.py`
- **test_tick_with_ddb_backend()** (10 connections) — `core/tests/test_cloud_reconcile.py`
- **_passed_worker_events()** (8 connections) — `core/tests/test_cloud_reconcile.py`
- **.records()** (7 connections) — `core/gherkai_core/adapters/event_log/ddb.py`
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
- *... and 36 more nodes in this community*

## Relationships

- [Engine Ports & Adapters](Engine_Ports_%26_Adapters.md) (21 shared connections)
- [SQLite Event Log & Projection](SQLite_Event_Log_%26_Projection.md) (12 shared connections)
- [Run State Rendering & Boto Guard](Run_State_Rendering_%26_Boto_Guard.md) (11 shared connections)
- [DynamoDB RunStore Conditional Writes](DynamoDB_RunStore_Conditional_Writes.md) (4 shared connections)
- [Reconciler Lambda & Timeouts](Reconciler_Lambda_%26_Timeouts.md) (3 shared connections)
- [Fargate Engine Unit Tests](Fargate_Engine_Unit_Tests.md) (3 shared connections)
- [Reconcile Ports & Tick](Reconcile_Ports_%26_Tick.md) (3 shared connections)
- [Run Result Verdict Model](Run_Result_Verdict_Model.md) (3 shared connections)
- [Fargate Event Drain & Exit Codes](Fargate_Event_Drain_%26_Exit_Codes.md) (2 shared connections)
- [Run Schedule Orchestration](Run_Schedule_Orchestration.md) (2 shared connections)
- [Exit Item Test Setup](Exit_Item_Test_Setup.md) (1 shared connections)
- [Exit Observer Lambda](Exit_Observer_Lambda.md) (1 shared connections)

## Source Files

- `core/gherkai_core/adapters/cloud_launcher.py`
- `core/gherkai_core/adapters/event_log/__init__.py`
- `core/gherkai_core/adapters/event_log/ddb.py`
- `core/gherkai_core/adapters/fargate_engine.py`
- `core/tests/test_cloud_reconcile.py`

## Audit Trail

- EXTRACTED: 155 (86%)
- INFERRED: 25 (14%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*