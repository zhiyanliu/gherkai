# DynamoDB Job State Store

> 57 nodes · cohesion 0.08

## Key Concepts

- **JobState** (101 connections) — `core/gherkai_core/model.py`
- **test_stores.py** (56 connections) — `core/tests/test_stores.py`
- **_sample_run()** (39 connections) — `core/tests/test_stores.py`
- **test_ddb_run_store.py** (24 connections) — `core/tests/test_ddb_run_store.py`
- **run_store/ddb.py** (20 connections) — `core/gherkai_core/adapters/run_store/ddb.py`
- **run_meta_from_dict()** (16 connections) — `core/gherkai_core/serialize.py`
- **run_meta_to_dict()** (16 connections) — `core/gherkai_core/serialize.py`
- **run_state_from_result()** (10 connections) — `core/gherkai_core/model.py`
- **from_dict()** (10 connections) — `core/gherkai_core/serialize.py`
- **Path** (10 connections)
- **to_dict()** (9 connections) — `core/gherkai_core/serialize.py`
- **_initial_state()** (9 connections) — `core/tests/test_stores.py`
- **test_ddb_session_id_none_omitted_real()** (7 connections) — `core/tests/test_cloud_integration.py`
- **test_job_state_claimed_at_round_trip()** (6 connections) — `core/tests/test_stores.py`
- **test_realtime_write_lifecycle()** (6 connections) — `core/tests/test_stores.py`
- **test_run_state_jobs_map_round_trip()** (6 connections) — `core/tests/test_stores.py`
- **test_run_state_timestamps_round_trip()** (6 connections) — `core/tests/test_stores.py`
- **test_step_message_survives_round_trip_and_missing_key_is_none()** (6 connections) — `core/tests/test_stores.py`
- **.load_run_state()** (5 connections) — `core/gherkai_core/adapters/run_store/ddb.py`
- **_job_state_to_item()** (5 connections) — `core/gherkai_core/adapters/run_store/ddb.py`
- **test_run_meta_extra_http_headers_multiple_normalize_at_write_side()** (5 connections) — `core/tests/test_stores.py`
- **test_run_meta_steps_dir_round_trip()** (5 connections) — `core/tests/test_stores.py`
- **test_run_meta_worker_fields_round_trip()** (5 connections) — `core/tests/test_stores.py`
- **test_run_state_omits_null_timestamps()** (5 connections) — `core/tests/test_stores.py`
- **test_run_store_save_load()** (5 connections) — `core/tests/test_stores.py`
- *... and 32 more nodes in this community*

## Relationships

- [Job Explain Data Model](Job_Explain_Data_Model.md) (49 shared connections)
- [Run State Store](Run_State_Store.md) (36 shared connections)
- [Cloud Adapter Boundary Modules](Cloud_Adapter_Boundary_Modules.md) (24 shared connections)
- [Result Store Adapters](Result_Store_Adapters.md) (20 shared connections)
- [S3 Result Store](S3_Result_Store.md) (11 shared connections)
- [Explain Reads And Report Store](Explain_Reads_And_Report_Store.md) (8 shared connections)
- [Conditional Write Guards](Conditional_Write_Guards.md) (7 shared connections)
- [Reconciler Event Projection](Reconciler_Event_Projection.md) (6 shared connections)
- [EventLog And Launcher Ports](EventLog_And_Launcher_Ports.md) (6 shared connections)
- [Step Argument S3 Offload](Step_Argument_S3_Offload.md) (5 shared connections)
- [Lambda Handler Event Parsing Tests](Lambda_Handler_Event_Parsing_Tests.md) (5 shared connections)
- [Result Tree Rendering](Result_Tree_Rendering.md) (5 shared connections)

## Source Files

- `core/gherkai_core/adapters/run_store/ddb.py`
- `core/gherkai_core/model.py`
- `core/gherkai_core/serialize.py`
- `core/tests/test_cloud_integration.py`
- `core/tests/test_ddb_run_store.py`
- `core/tests/test_stores.py`

## Audit Trail

- EXTRACTED: 309 (92%)
- INFERRED: 26 (8%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*