# Cloud Launcher and EventLog

> 54 nodes · cohesion 0.07

## Key Concepts

- **test_cloud_reconcile.py** (38 connections) — `core/tests/test_cloud_reconcile.py`
- **DdbEventLog** (25 connections) — `core/gherkai_core/adapters/event_log/ddb.py`
- **CloudLauncher** (17 connections) — `core/gherkai_core/adapters/cloud_launcher.py`
- **_RecorderWatch** (15 connections) — `core/tests/test_cloud_reconcile.py`
- **_FakeStartEngine** (14 connections) — `core/tests/test_cloud_reconcile.py`
- **_job()** (11 connections) — `core/tests/test_cloud_reconcile.py`
- **test_tick_with_ddb_backend()** (10 connections) — `core/tests/test_cloud_reconcile.py`
- **EventBridgeTimeoutWatch** (9 connections) — `deploy_aws/gherkai_deploy_aws/lambdas/reconciler.py`
- **_passed_worker_events()** (8 connections) — `core/tests/test_cloud_reconcile.py`
- **_build()** (8 connections) — `deploy_aws/gherkai_deploy_aws/lambdas/reconciler.py`
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
- *... and 29 more nodes in this community*

## Relationships

- [Run Definition Domain Model](Run_Definition_Domain_Model.md) (19 shared connections)
- [Event Keys & Exit Records](Event_Keys_%26_Exit_Records.md) (6 shared connections)
- [Exit Observer Lambda](Exit_Observer_Lambda.md) (5 shared connections)
- [Result Tree Text Rendering](Result_Tree_Text_Rendering.md) (5 shared connections)
- [DynamoDB Run Store](DynamoDB_Run_Store.md) (4 shared connections)
- [Run State Rendering](Run_State_Rendering.md) (4 shared connections)
- [Core Adapters Documentation](Core_Adapters_Documentation.md) (3 shared connections)
- [Event Records Projection](Event_Records_Projection.md) (3 shared connections)
- [State Projection Tests](State_Projection_Tests.md) (3 shared connections)
- [Reconcile Tick and Report](Reconcile_Tick_and_Report.md) (3 shared connections)
- [SQLite Event Log](SQLite_Event_Log.md) (2 shared connections)
- [Boto3 Adapter Guard](Boto3_Adapter_Guard.md) (2 shared connections)

## Source Files

- `core/gherkai_core/adapters/cloud_launcher.py`
- `core/gherkai_core/adapters/event_log/ddb.py`
- `core/tests/test_cloud_reconcile.py`
- `deploy_aws/gherkai_deploy_aws/lambdas/reconciler.py`

## Audit Trail

- EXTRACTED: 134 (82%)
- INFERRED: 29 (18%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*