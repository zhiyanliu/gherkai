# Reconcile Tick and Report

> 40 nodes · cohesion 0.10

## Key Concepts

- **test_reconcile.py** (35 connections) — `core/tests/test_reconcile.py`
- **tick()** (25 connections) — `core/gherkai_core/reconcile.py`
- **FakeLauncher** (18 connections) — `core/tests/test_reconcile.py`
- **_setup()** (16 connections) — `core/tests/test_reconcile.py`
- **_RecordingResultStore** (12 connections) — `core/tests/test_reconcile.py`
- **test_finalize_writes_verdicts_before_commit_point()** (11 connections) — `core/tests/test_reconcile.py`
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
- **.launch()** (2 connections) — `core/tests/test_reconcile.py`
- **Job** (2 connections)
- **done 后写 RunReport（派生视图，**永远最后**；ADR 0030 决定三 / 0034 收尾）。宿主在 tick 返回 done 后调。…** (1 connections) — `core/gherkai_core/reconcile.py`
- **推进一步。返回 run 是否已达终态（全 done 且 finalize 成功/已被别人 finalize）。 幂等：可反复调、并发调。步骤（ADR 0034…** (1 connections) — `core/gherkai_core/reconcile.py`
- **.__init__()** (1 connections) — `core/tests/test_reconcile.py`
- *... and 15 more nodes in this community*

## Relationships

- [Run Definition Domain Model](Run_Definition_Domain_Model.md) (21 shared connections)
- [Core Adapters Documentation](Core_Adapters_Documentation.md) (8 shared connections)
- [Run State Rendering](Run_State_Rendering.md) (8 shared connections)
- [DynamoDB Run Store](DynamoDB_Run_Store.md) (5 shared connections)
- [SQLite Event Log](SQLite_Event_Log.md) (4 shared connections)
- [Exit Observer Lambda](Exit_Observer_Lambda.md) (4 shared connections)
- [Cloud Launcher and EventLog](Cloud_Launcher_and_EventLog.md) (3 shared connections)
- [Result Tree Text Rendering](Result_Tree_Text_Rendering.md) (3 shared connections)
- [Event Records Projection](Event_Records_Projection.md) (2 shared connections)
- [Detached Reconcile Loop Tests](Detached_Reconcile_Loop_Tests.md) (2 shared connections)
- [Reconciler Plan Next](Reconciler_Plan_Next.md) (1 shared connections)
- [State Projection Tests](State_Projection_Tests.md) (1 shared connections)

## Source Files

- `core/gherkai_core/reconcile.py`
- `core/tests/test_reconcile.py`
- `deploy_aws/gherkai_deploy_aws/lambdas/reconciler.py`

## Audit Trail

- EXTRACTED: 126 (89%)
- INFERRED: 16 (11%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*