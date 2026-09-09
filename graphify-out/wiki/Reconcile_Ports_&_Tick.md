# Reconcile Ports & Tick

> 40 nodes · cohesion 0.09

## Key Concepts

- **test_reconcile.py** (29 connections) — `core/tests/test_reconcile.py`
- **tick()** (21 connections) — `core/gherkai_core/reconcile.py`
- **FakeLauncher** (16 connections) — `core/tests/test_reconcile.py`
- **_setup()** (14 connections) — `core/tests/test_reconcile.py`
- **BoomLauncher** (12 connections) — `core/tests/test_reconcile.py`
- **EventLog** (9 connections) — `core/gherkai_core/reconcile.py`
- **Launcher** (8 connections) — `core/gherkai_core/reconcile.py`
- **_done_events()** (6 connections) — `core/tests/test_reconcile.py`
- **test_double_finalize_idempotent()** (6 connections) — `core/tests/test_reconcile.py`
- **test_tick_finalizes_when_all_done()** (6 connections) — `core/tests/test_reconcile.py`
- **test_tick_starts_next_after_completion()** (6 connections) — `core/tests/test_reconcile.py`
- **test_launch_failure_does_not_wedge_run()** (5 connections) — `core/tests/test_reconcile.py`
- **test_launch_failure_isolated_other_job_completes()** (5 connections) — `core/tests/test_reconcile.py`
- **test_tick_idempotent_no_double_launch()** (5 connections) — `core/tests/test_reconcile.py`
- **test_tick_nonzero_exit_finalizes_error()** (5 connections) — `core/tests/test_reconcile.py`
- **_meta()** (4 connections) — `core/tests/test_reconcile.py`
- **test_first_tick_starts_up_to_concurrency()** (4 connections) — `core/tests/test_reconcile.py`
- **.launch()** (2 connections) — `core/gherkai_core/reconcile.py`
- **Protocol** (2 connections)
- **.launch()** (2 connections) — `core/tests/test_reconcile.py`
- **.launch()** (2 connections) — `core/tests/test_reconcile.py`
- **Job** (2 connections)
- **.record_exit()** (1 connections) — `core/gherkai_core/reconcile.py`
- **.records()** (1 connections) — `core/gherkai_core/reconcile.py`
- **Job** (1 connections)
- *... and 15 more nodes in this community*

## Relationships

- [Engine Ports & Adapters](Engine_Ports_%26_Adapters.md) (16 shared connections)
- [Run State Rendering & Boto Guard](Run_State_Rendering_%26_Boto_Guard.md) (15 shared connections)
- [Run Result Verdict Model](Run_Result_Verdict_Model.md) (7 shared connections)
- [DynamoDB RunStore Conditional Writes](DynamoDB_RunStore_Conditional_Writes.md) (6 shared connections)
- [Cloud Launcher & DDB EventLog](Cloud_Launcher_%26_DDB_EventLog.md) (3 shared connections)
- [SQLite Event Log & Projection](SQLite_Event_Log_%26_Projection.md) (2 shared connections)
- [SQLite Event Log Store](SQLite_Event_Log_Store.md) (2 shared connections)
- [Reconcile Loop Integration](Reconcile_Loop_Integration.md) (1 shared connections)
- [Reconciler Lambda & Timeouts](Reconciler_Lambda_%26_Timeouts.md) (1 shared connections)

## Source Files

- `core/gherkai_core/reconcile.py`
- `core/tests/test_reconcile.py`

## Audit Trail

- EXTRACTED: 100 (83%)
- INFERRED: 21 (17%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*