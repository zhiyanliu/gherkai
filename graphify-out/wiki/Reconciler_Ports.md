# Reconciler Ports

> 50 nodes · cohesion 0.07

## Key Concepts

- **test_reconcile.py** (35 connections) — `core/tests/test_reconcile.py`
- **tick()** (25 connections) — `core/gherkai_core/reconcile.py`
- **FakeLauncher** (18 connections) — `core/tests/test_reconcile.py`
- **_setup()** (16 connections) — `core/tests/test_reconcile.py`
- **_RecordingResultStore** (12 connections) — `core/tests/test_reconcile.py`
- **EventLog** (11 connections) — `core/gherkai_core/reconcile.py`
- **test_finalize_writes_verdicts_before_commit_point()** (11 connections) — `core/tests/test_reconcile.py`
- **Launcher** (9 connections) — `core/gherkai_core/reconcile.py`
- **_done_events()** (9 connections) — `core/tests/test_reconcile.py`
- **_tick_runs()** (8 connections) — `deploy_aws/gherkai_deploy_aws/lambdas/reconciler.py`
- **finalize_report()** (7 connections) — `core/gherkai_core/reconcile.py`
- **test_verdict_write_failure_fails_tick_before_commit_and_retry_heals()** (7 connections) — `core/tests/test_reconcile.py`
- **test_double_finalize_idempotent()** (6 connections) — `core/tests/test_reconcile.py`
- **test_tick_finalizes_when_all_done()** (6 connections) — `core/tests/test_reconcile.py`
- **test_tick_starts_next_after_completion()** (6 connections) — `core/tests/test_reconcile.py`
- **_meta()** (5 connections) — `core/tests/test_reconcile.py`
- **test_finalize_report_passes_run_duration_into_the_report()** (5 connections) — `core/tests/test_reconcile.py`
- **test_launch_failure_does_not_wedge_run()** (5 connections) — `core/tests/test_reconcile.py`
- **test_launch_failure_isolated_other_job_completes()** (5 connections) — `core/tests/test_reconcile.py`
- **test_tick_idempotent_no_double_launch()** (5 connections) — `core/tests/test_reconcile.py`
- **test_tick_nonzero_exit_finalizes_error()** (5 connections) — `core/tests/test_reconcile.py`
- **test_first_tick_starts_up_to_concurrency()** (4 connections) — `core/tests/test_reconcile.py`
- **.launch()** (2 connections) — `core/gherkai_core/reconcile.py`
- **Protocol** (2 connections)
- **.launch()** (2 connections) — `core/tests/test_reconcile.py`
- *... and 25 more nodes in this community*

## Relationships

- [Job Explain & S3 Offload](Job_Explain_%26_S3_Offload.md) (25 shared connections)
- [Run State Projection](Run_State_Projection.md) (9 shared connections)
- [DynamoDB RunStore Adapter](DynamoDB_RunStore_Adapter.md) (8 shared connections)
- [S3 Report Store & Control Plane](S3_Report_Store_%26_Control_Plane.md) (6 shared connections)
- [SQLite Event Log](SQLite_Event_Log.md) (5 shared connections)
- [Run State Rendering](Run_State_Rendering.md) (5 shared connections)
- [Reconciler Lambda](Reconciler_Lambda.md) (5 shared connections)
- [Cloud Boto3 Guards & EventLog](Cloud_Boto3_Guards_%26_EventLog.md) (4 shared connections)
- [Cloud Job Launcher](Cloud_Job_Launcher.md) (3 shared connections)

## Source Files

- `core/gherkai_core/reconcile.py`
- `core/tests/test_reconcile.py`
- `deploy_aws/gherkai_deploy_aws/lambdas/reconciler.py`

## Audit Trail

- EXTRACTED: 137 (85%)
- INFERRED: 24 (15%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*