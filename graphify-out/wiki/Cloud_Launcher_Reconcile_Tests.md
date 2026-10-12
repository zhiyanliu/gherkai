# Cloud Launcher Reconcile Tests

> 47 nodes · cohesion 0.08

## Key Concepts

- **test_cloud_reconcile.py** (38 connections) — `core/tests/test_cloud_reconcile.py`
- **DdbEventLog** (25 connections) — `core/gherkai_core/adapters/event_log/ddb.py`
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
- **test_ddb_record_exit_reason_roundtrip()** (4 connections) — `core/tests/test_cloud_reconcile.py`
- **test_ddb_event_log_queries_with_consistent_read()** (3 connections) — `core/tests/test_cloud_reconcile.py`
- **test_ddb_event_log_reads_worker_events()** (3 connections) — `core/tests/test_cloud_reconcile.py`
- **.launch()** (2 connections) — `core/gherkai_core/adapters/cloud_launcher.py`
- **.__init__()** (1 connections) — `core/gherkai_core/adapters/cloud_launcher.py`
- *... and 22 more nodes in this community*

## Relationships

- [Job Explain Data Model](Job_Explain_Data_Model.md) (18 shared connections)
- [Cloud Adapter Boundary Modules](Cloud_Adapter_Boundary_Modules.md) (9 shared connections)
- [Event Exit Records & Keys](Event_Exit_Records_%26_Keys.md) (6 shared connections)
- [Reconcile Lambdas](Reconcile_Lambdas.md) (4 shared connections)
- [Reconciler Event Projection](Reconciler_Event_Projection.md) (4 shared connections)
- [DynamoDB Job State Store](DynamoDB_Job_State_Store.md) (4 shared connections)
- [Run State Store](Run_State_Store.md) (4 shared connections)
- [Detached Local Run Host](Detached_Local_Run_Host.md) (2 shared connections)
- [Event Wire Protocol](Event_Wire_Protocol.md) (2 shared connections)
- [EventLog And Launcher Ports](EventLog_And_Launcher_Ports.md) (2 shared connections)
- [Run Scheduling Events Core](Run_Scheduling_Events_Core.md) (2 shared connections)
- [Worker Exit Drain Tests](Worker_Exit_Drain_Tests.md) (1 shared connections)

## Source Files

- `core/gherkai_core/adapters/cloud_launcher.py`
- `core/gherkai_core/adapters/event_log/ddb.py`
- `core/tests/test_cloud_reconcile.py`

## Audit Trail

- EXTRACTED: 122 (82%)
- INFERRED: 27 (18%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*