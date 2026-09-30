# Reconciler Orchestration

> 51 nodes · cohesion 0.07

## Key Concepts

- **test_reconcile.py** (35 connections) — `core/tests/test_reconcile.py`
- **tick()** (25 connections) — `core/gherkai_core/reconcile.py`
- **reconcile.py** (21 connections) — `core/gherkai_core/reconcile.py`
- **FakeLauncher** (18 connections) — `core/tests/test_reconcile.py`
- **_setup()** (16 connections) — `core/tests/test_reconcile.py`
- **_RecordingResultStore** (12 connections) — `core/tests/test_reconcile.py`
- **EventLog** (11 connections) — `core/gherkai_core/reconcile.py`
- **test_finalize_writes_verdicts_before_commit_point()** (11 connections) — `core/tests/test_reconcile.py`
- **Launcher** (9 connections) — `core/gherkai_core/reconcile.py`
- **_done_events()** (9 connections) — `core/tests/test_reconcile.py`
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
- *... and 26 more nodes in this community*

## Relationships

- [Job Domain Models](Job_Domain_Models.md) (30 shared connections)
- [Run Result Aggregation Tree](Run_Result_Aggregation_Tree.md) (13 shared connections)
- [Run State Projection](Run_State_Projection.md) (7 shared connections)
- [Cloud Store Adapters](Cloud_Store_Adapters.md) (6 shared connections)
- [Run State Store](Run_State_Store.md) (5 shared connections)
- [Reconciler Lambda](Reconciler_Lambda.md) (3 shared connections)
- [SQLite Event Log](SQLite_Event_Log.md) (3 shared connections)
- [Event Log Adapters](Event_Log_Adapters.md) (2 shared connections)
- [Local Reconcile Loop Tests](Local_Reconcile_Loop_Tests.md) (2 shared connections)
- [Cloud Reconcile Tests](Cloud_Reconcile_Tests.md) (2 shared connections)
- [Run Store Adapters](Run_Store_Adapters.md) (2 shared connections)
- [Local Detached Execution](Local_Detached_Execution.md) (1 shared connections)

## Source Files

- `core/DEVELOPMENT.md`
- `core/gherkai_core/reconcile.py`
- `core/tests/test_reconcile.py`

## Audit Trail

- EXTRACTED: 147 (86%)
- INFERRED: 24 (14%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*