# EventLog And Launcher Ports

> 52 nodes · cohesion 0.07

## Key Concepts

- **test_reconcile.py** (35 connections) — `core/tests/test_reconcile.py`
- **tick()** (25 connections) — `core/gherkai_core/reconcile.py`
- **FakeLauncher** (18 connections) — `core/tests/test_reconcile.py`
- **_setup()** (16 connections) — `core/tests/test_reconcile.py`
- **EventLog** (12 connections) — `core/gherkai_core/reconcile.py`
- **BoomLauncher** (12 connections) — `core/tests/test_reconcile.py`
- **_RecordingResultStore** (12 connections) — `core/tests/test_reconcile.py`
- **test_finalize_writes_verdicts_before_commit_point()** (11 connections) — `core/tests/test_reconcile.py`
- **Launcher** (10 connections) — `core/gherkai_core/reconcile.py`
- **_done_events()** (9 connections) — `core/tests/test_reconcile.py`
- **_job()** (7 connections) — `core/tests/test_reconcile.py`
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
- *... and 27 more nodes in this community*

## Relationships

- [Job Explain Data Model](Job_Explain_Data_Model.md) (27 shared connections)
- [Run State Store](Run_State_Store.md) (12 shared connections)
- [Cloud Adapter Boundary Modules](Cloud_Adapter_Boundary_Modules.md) (10 shared connections)
- [DynamoDB Job State Store](DynamoDB_Job_State_Store.md) (6 shared connections)
- [Reconciler Event Projection](Reconciler_Event_Projection.md) (5 shared connections)
- [Store Port Definitions](Store_Port_Definitions.md) (3 shared connections)
- [SQLite Event Log](SQLite_Event_Log.md) (3 shared connections)
- [Cloud Launcher Reconcile Tests](Cloud_Launcher_Reconcile_Tests.md) (2 shared connections)
- [Detached Launcher Reconcile Loop](Detached_Launcher_Reconcile_Loop.md) (1 shared connections)
- [Reconcile Lambdas](Reconcile_Lambdas.md) (1 shared connections)
- [Detached Local Run Host](Detached_Local_Run_Host.md) (1 shared connections)

## Source Files

- `core/DEVELOPMENT.md`
- `core/gherkai_core/reconcile.py`
- `core/tests/test_reconcile.py`

## Audit Trail

- EXTRACTED: 136 (82%)
- INFERRED: 30 (18%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*