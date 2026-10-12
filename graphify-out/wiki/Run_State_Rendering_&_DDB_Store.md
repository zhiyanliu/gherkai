# Run State Rendering & DDB Store

> 87 nodes · cohesion 0.04

## Key Concepts

- **RunState** (127 connections) — `core/gherkai_core/model.py`
- **test_conditional_writes.py** (40 connections) — `core/tests/test_conditional_writes.py`
- **_meta()** (25 connections) — `core/tests/test_conditional_writes.py`
- **_initial()** (24 connections) — `core/tests/test_conditional_writes.py`
- **test_stale_projection_never_regresses_terminal_job_on_real_ddb()** (9 connections) — `core/tests/test_conditional_writes.py`
- **.create_run()** (8 connections) — `core/gherkai_core/adapters/run_store/ddb.py`
- **.save_run()** (8 connections) — `core/gherkai_core/adapters/run_store/local.py`
- **._write_state()** (8 connections) — `core/gherkai_core/adapters/run_store/local.py`
- **test_explain_cloud_not_landed_hint_carries_cloud_locator_flags()** (7 connections) — `cli/tests/test_main.py`
- **.load_run_state()** (7 connections) — `core/gherkai_core/adapters/run_store/local.py`
- **test_claim_is_exclusive_on_real_ddb()** (7 connections) — `core/tests/test_conditional_writes.py`
- **test_projection_lands_running_once_any_job_advanced()** (7 connections) — `core/tests/test_conditional_writes.py`
- **test_projection_preserves_claimed_at()** (7 connections) — `core/tests/test_conditional_writes.py`
- **test_projection_without_baseline_keeps_stored_lineage()** (7 connections) — `core/tests/test_conditional_writes.py`
- **test_render_status_pending_run_with_claimed_job_does_not_hint()** (6 connections) — `cli/tests/test_main.py`
- **_atomic_write_json()** (6 connections) — `core/gherkai_core/adapters/run_store/local.py`
- **.finalize_run()** (6 connections) — `core/gherkai_core/adapters/run_store/local.py`
- **.update_job_state()** (6 connections) — `core/gherkai_core/adapters/run_store/local.py`
- **run_state_from_dict()** (6 connections) — `core/gherkai_core/serialize.py`
- **run_state_to_dict()** (6 connections) — `core/gherkai_core/serialize.py`
- **test_projection_never_lands_terminal_run_status()** (6 connections) — `core/tests/test_conditional_writes.py`
- **test_projection_with_unknown_scope_is_ignored_not_invented()** (6 connections) — `core/tests/test_conditional_writes.py`
- **test_same_hwm_terminal_job_not_regressed()** (6 connections) — `core/tests/test_conditional_writes.py`
- **test_stale_projection_rejected()** (6 connections) — `core/tests/test_conditional_writes.py`
- **.save_run()** (5 connections) — `core/gherkai_core/adapters/run_store/ddb.py`
- *... and 62 more nodes in this community*

## Relationships

- [Cloud Launcher & Fargate Adapters](Cloud_Launcher_%26_Fargate_Adapters.md) (34 shared connections)
- [Job/Scenario Explain Model](Job-Scenario_Explain_Model.md) (33 shared connections)
- [Job State Serialization](Job_State_Serialization.md) (29 shared connections)
- [SQLite Event Log Adapter](SQLite_Event_Log_Adapter.md) (25 shared connections)
- [Fake DDB Table & SQLite Records](Fake_DDB_Table_%26_SQLite_Records.md) (20 shared connections)
- [Reconcile Tick & Report Finalize](Reconcile_Tick_%26_Report_Finalize.md) (5 shared connections)
- [Result Rendering & Explain](Result_Rendering_%26_Explain.md) (4 shared connections)
- [Lambda Handler Event Parsing Tests](Lambda_Handler_Event_Parsing_Tests.md) (4 shared connections)
- [Cloud Resource Preflight](Cloud_Resource_Preflight.md) (4 shared connections)
- [CLI Command Dispatch Entry](CLI_Command_Dispatch_Entry.md) (3 shared connections)
- [Plan & Explain Rendering](Plan_%26_Explain_Rendering.md) (3 shared connections)
- [S3 Result Store](S3_Result_Store.md) (3 shared connections)

## Source Files

- `cli/tests/test_main.py`
- `cli/tests/test_render.py`
- `core/gherkai_core/adapters/run_store/ddb.py`
- `core/gherkai_core/adapters/run_store/local.py`
- `core/gherkai_core/model.py`
- `core/gherkai_core/persist.py`
- `core/gherkai_core/ports.py`
- `core/gherkai_core/serialize.py`
- `core/tests/test_conditional_writes.py`

## Audit Trail

- EXTRACTED: 303 (90%)
- INFERRED: 34 (10%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*