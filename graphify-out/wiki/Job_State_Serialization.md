# Job State Serialization

> 72 nodes · cohesion 0.06

## Key Concepts

- **JobState** (101 connections) — `core/gherkai_core/model.py`
- **test_stores.py** (56 connections) — `core/tests/test_stores.py`
- **_sample_run()** (39 connections) — `core/tests/test_stores.py`
- **test_cloud_integration.py** (32 connections) — `core/tests/test_cloud_integration.py`
- **test_ddb_run_store.py** (24 connections) — `core/tests/test_ddb_run_store.py`
- **run_meta_from_dict()** (16 connections) — `core/gherkai_core/serialize.py`
- **run_meta_to_dict()** (16 connections) — `core/gherkai_core/serialize.py`
- **run_state_from_result()** (10 connections) — `core/gherkai_core/model.py`
- **from_dict()** (10 connections) — `core/gherkai_core/serialize.py`
- **_uniq()** (10 connections) — `core/tests/test_cloud_integration.py`
- **Path** (10 connections)
- **to_dict()** (9 connections) — `core/gherkai_core/serialize.py`
- **_ddb_store()** (9 connections) — `core/tests/test_cloud_integration.py`
- **_initial_state()** (9 connections) — `core/tests/test_stores.py`
- **test_ddb_state_item_grows_past_400kb_on_incremental_update_real()** (8 connections) — `core/tests/test_cloud_integration.py`
- **test_ddb_empty_string_scalar_and_map_entry_real()** (7 connections) — `core/tests/test_cloud_integration.py`
- **test_ddb_run_store_lifecycle_real()** (7 connections) — `core/tests/test_cloud_integration.py`
- **test_ddb_session_id_none_omitted_real()** (7 connections) — `core/tests/test_cloud_integration.py`
- **test_job_state_claimed_at_round_trip()** (6 connections) — `core/tests/test_stores.py`
- **test_realtime_write_lifecycle()** (6 connections) — `core/tests/test_stores.py`
- **test_run_state_jobs_map_round_trip()** (6 connections) — `core/tests/test_stores.py`
- **test_run_state_timestamps_round_trip()** (6 connections) — `core/tests/test_stores.py`
- **_job_state_to_item()** (5 connections) — `core/gherkai_core/adapters/run_store/ddb.py`
- **test_ddb_update_before_create_raises_real()** (5 connections) — `core/tests/test_cloud_integration.py`
- **test_s3_result_store_round_trip_real()** (5 connections) — `core/tests/test_cloud_integration.py`
- *... and 47 more nodes in this community*

## Relationships

- [Job/Scenario Explain Model](Job-Scenario_Explain_Model.md) (41 shared connections)
- [Cloud Launcher & Fargate Adapters](Cloud_Launcher_%26_Fargate_Adapters.md) (37 shared connections)
- [S3 Result Store](S3_Result_Store.md) (31 shared connections)
- [Run State Rendering & DDB Store](Run_State_Rendering_%26_DDB_Store.md) (29 shared connections)
- [SQLite Event Log Adapter](SQLite_Event_Log_Adapter.md) (23 shared connections)
- [Result Rendering & Explain](Result_Rendering_%26_Explain.md) (10 shared connections)
- [Fake DDB Table & SQLite Records](Fake_DDB_Table_%26_SQLite_Records.md) (7 shared connections)
- [Local Result Store & Persistence](Local_Result_Store_%26_Persistence.md) (5 shared connections)
- [Reconcile Tick & Report Finalize](Reconcile_Tick_%26_Report_Finalize.md) (5 shared connections)
- [Lambda Handler Event Parsing Tests](Lambda_Handler_Event_Parsing_Tests.md) (4 shared connections)
- [Cloud Reconcile Launcher Tests](Cloud_Reconcile_Launcher_Tests.md) (3 shared connections)
- [Local Report Store](Local_Report_Store.md) (2 shared connections)

## Source Files

- `core/gherkai_core/adapters/run_store/ddb.py`
- `core/gherkai_core/model.py`
- `core/gherkai_core/ports.py`
- `core/gherkai_core/serialize.py`
- `core/tests/test_cloud_integration.py`
- `core/tests/test_ddb_run_store.py`
- `core/tests/test_project.py`
- `core/tests/test_stores.py`

## Audit Trail

- EXTRACTED: 345 (93%)
- INFERRED: 27 (7%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*