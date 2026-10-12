# Reconcile Tick & Report Finalize

> 39 nodes · cohesion 0.11

## Key Concepts

- **test_reconcile.py** (35 connections) — `core/tests/test_reconcile.py`
- **tick()** (25 connections) — `core/gherkai_core/reconcile.py`
- **FakeLauncher** (18 connections) — `core/tests/test_reconcile.py`
- **_setup()** (16 connections) — `core/tests/test_reconcile.py`
- **_RecordingResultStore** (12 connections) — `core/tests/test_reconcile.py`
- **test_finalize_writes_verdicts_before_commit_point()** (11 connections) — `core/tests/test_reconcile.py`
- **finalize_report()** (9 connections) — `core/gherkai_core/reconcile.py`
- **_done_events()** (9 connections) — `core/tests/test_reconcile.py`
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
- **ReportStore adapters (local / s3)** (4 connections) — `core/DEVELOPMENT.md`
- **test_first_tick_starts_up_to_concurrency()** (4 connections) — `core/tests/test_reconcile.py`
- **.launch()** (2 connections) — `core/tests/test_reconcile.py`
- **Job** (2 connections)
- **done 后写 RunReport（派生视图，**永远最后**；ADR 0030 决定三 / 0034 收尾）。宿主在 tick 返回 done 后调。…** (1 connections) — `core/gherkai_core/reconcile.py`
- **推进一步。返回 run 是否已达终态（全 done 且 finalize 成功/已被别人 finalize）。 幂等：可反复调、并发调。步骤（ADR 0034…** (1 connections) — `core/gherkai_core/reconcile.py`
- **.__init__()** (1 connections) — `core/tests/test_reconcile.py`
- *... and 14 more nodes in this community*

## Relationships

- [Cloud Launcher & Fargate Adapters](Cloud_Launcher_%26_Fargate_Adapters.md) (17 shared connections)
- [Job/Scenario Explain Model](Job-Scenario_Explain_Model.md) (16 shared connections)
- [SQLite Event Log Adapter](SQLite_Event_Log_Adapter.md) (9 shared connections)
- [Job State Serialization](Job_State_Serialization.md) (5 shared connections)
- [Run State Rendering & DDB Store](Run_State_Rendering_%26_DDB_Store.md) (5 shared connections)
- [Fake DDB Table & SQLite Records](Fake_DDB_Table_%26_SQLite_Records.md) (4 shared connections)
- [Exit Observer Lambda](Exit_Observer_Lambda.md) (3 shared connections)
- [Atomic Local File Writes](Atomic_Local_File_Writes.md) (1 shared connections)
- [Cloud Store Composition Root](Cloud_Store_Composition_Root.md) (1 shared connections)
- [DynamoDB Event Log](DynamoDB_Event_Log.md) (1 shared connections)
- [Cloud Reconcile Launcher Tests](Cloud_Reconcile_Launcher_Tests.md) (1 shared connections)

## Source Files

- `core/DEVELOPMENT.md`
- `core/gherkai_core/reconcile.py`
- `core/tests/test_reconcile.py`

## Audit Trail

- EXTRACTED: 124 (88%)
- INFERRED: 17 (12%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*