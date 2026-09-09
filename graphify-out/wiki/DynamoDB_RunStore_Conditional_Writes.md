# DynamoDB RunStore Conditional Writes

> 88 nodes · cohesion 0.05

## Key Concepts

- **JobState** (85 connections) — `core/gherkai_core/model.py`
- **test_stores.py** (55 connections) — `core/tests/test_stores.py`
- **LocalRunStore** (48 connections) — `core/gherkai_core/adapters/run_store/local.py`
- **_sample_run()** (38 connections) — `core/tests/test_stores.py`
- **DynamoDBRunStore** (37 connections) — `core/gherkai_core/adapters/run_store/ddb.py`
- **test_cloud_integration.py** (28 connections) — `core/tests/test_cloud_integration.py`
- **test_ddb_run_store.py** (24 connections) — `core/tests/test_ddb_run_store.py`
- **run_state_from_result()** (10 connections) — `core/gherkai_core/model.py`
- **from_dict()** (10 connections) — `core/gherkai_core/serialize.py`
- **_uniq()** (10 connections) — `core/tests/test_cloud_integration.py`
- **Path** (10 connections)
- **to_dict()** (9 connections) — `core/gherkai_core/serialize.py`
- **_ddb_store()** (9 connections) — `core/tests/test_cloud_integration.py`
- **test_detached_flag_on_state_item()** (9 connections) — `core/tests/test_ddb_run_store.py`
- **test_worker_task_def_arns_on_state_item()** (9 connections) — `core/tests/test_ddb_run_store.py`
- **_initial_state()** (9 connections) — `core/tests/test_stores.py`
- **test_ddb_state_item_grows_past_400kb_on_incremental_update_real()** (8 connections) — `core/tests/test_cloud_integration.py`
- **._locked_rmw()** (7 connections) — `core/gherkai_core/adapters/run_store/local.py`
- **test_ddb_empty_string_scalar_and_map_entry_real()** (7 connections) — `core/tests/test_cloud_integration.py`
- **test_ddb_run_store_lifecycle_real()** (7 connections) — `core/tests/test_cloud_integration.py`
- **test_ddb_session_id_none_omitted_real()** (7 connections) — `core/tests/test_cloud_integration.py`
- **test_job_state_claimed_at_round_trip()** (6 connections) — `core/tests/test_stores.py`
- **test_realtime_write_lifecycle()** (6 connections) — `core/tests/test_stores.py`
- **test_run_state_jobs_map_round_trip()** (6 connections) — `core/tests/test_stores.py`
- **test_run_state_timestamps_round_trip()** (6 connections) — `core/tests/test_stores.py`
- *... and 63 more nodes in this community*

## Relationships

- [Run State Rendering & Boto Guard](Run_State_Rendering_%26_Boto_Guard.md) (70 shared connections)
- [Engine Ports & Adapters](Engine_Ports_%26_Adapters.md) (39 shared connections)
- [Run Result Verdict Model](Run_Result_Verdict_Model.md) (33 shared connections)
- [ResultStore Local/S3](ResultStore_Local-S3.md) (13 shared connections)
- [Run Persistence Orchestration](Run_Persistence_Orchestration.md) (10 shared connections)
- [SQLite Event Log & Projection](SQLite_Event_Log_%26_Projection.md) (10 shared connections)
- [Conditional Write Contract Tests](Conditional_Write_Contract_Tests.md) (8 shared connections)
- [Detached Launcher Reconcile](Detached_Launcher_Reconcile.md) (7 shared connections)
- [Reconcile Ports & Tick](Reconcile_Ports_%26_Tick.md) (6 shared connections)
- [Render & ReportStore Local](Render_%26_ReportStore_Local.md) (6 shared connections)
- [Cloud Launcher & DDB EventLog](Cloud_Launcher_%26_DDB_EventLog.md) (4 shared connections)
- [Cloud Adapter Test Fixtures](Cloud_Adapter_Test_Fixtures.md) (3 shared connections)

## Source Files

- `core/gherkai_core/adapters/run_store/ddb.py`
- `core/gherkai_core/adapters/run_store/local.py`
- `core/gherkai_core/model.py`
- `core/gherkai_core/serialize.py`
- `core/tests/test_cloud_integration.py`
- `core/tests/test_conditional_writes.py`
- `core/tests/test_ddb_run_store.py`
- `core/tests/test_stores.py`

## Audit Trail

- EXTRACTED: 379 (91%)
- INFERRED: 36 (9%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*