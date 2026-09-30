# DynamoDB Run Store

> 59 nodes · cohesion 0.06

## Key Concepts

- **JobState** (101 connections) — `core/gherkai_core/model.py`
- **DynamoDBRunStore** (40 connections) — `core/gherkai_core/adapters/run_store/ddb.py`
- **test_cloud_integration.py** (28 connections) — `core/tests/test_cloud_integration.py`
- **test_ddb_run_store.py** (24 connections) — `core/tests/test_ddb_run_store.py`
- **test_offload_unblocks_oversized_docstring_real()** (12 connections) — `core/tests/test_cloud_integration.py`
- **test_offload_round_trip_real()** (11 connections) — `core/tests/test_cloud_integration.py`
- **_uniq()** (10 connections) — `core/tests/test_cloud_integration.py`
- **test_detached_flag_on_state_item()** (10 connections) — `core/tests/test_ddb_run_store.py`
- **test_worker_task_def_arns_on_state_item()** (10 connections) — `core/tests/test_ddb_run_store.py`
- **_ddb_store()** (9 connections) — `core/tests/test_cloud_integration.py`
- **_initial_state()** (9 connections) — `core/tests/test_stores.py`
- **.create_run()** (8 connections) — `core/gherkai_core/adapters/run_store/ddb.py`
- **test_ddb_state_item_grows_past_400kb_on_incremental_update_real()** (8 connections) — `core/tests/test_cloud_integration.py`
- **test_ddb_empty_string_scalar_and_map_entry_real()** (7 connections) — `core/tests/test_cloud_integration.py`
- **test_ddb_run_store_lifecycle_real()** (7 connections) — `core/tests/test_cloud_integration.py`
- **test_ddb_session_id_none_omitted_real()** (7 connections) — `core/tests/test_cloud_integration.py`
- **.load_run_state()** (5 connections) — `core/gherkai_core/adapters/run_store/ddb.py`
- **.save_run()** (5 connections) — `core/gherkai_core/adapters/run_store/ddb.py`
- **_job_state_to_item()** (5 connections) — `core/gherkai_core/adapters/run_store/ddb.py`
- **test_ddb_update_before_create_raises_real()** (5 connections) — `core/tests/test_cloud_integration.py`
- **test_s3_result_store_round_trip_real()** (5 connections) — `core/tests/test_cloud_integration.py`
- **.update_job_state()** (4 connections) — `core/gherkai_core/adapters/run_store/ddb.py`
- **_job_state_from_item()** (4 connections) — `core/gherkai_core/adapters/run_store/ddb.py`
- **_is_ddb_too_large()** (4 connections) — `core/tests/test_cloud_integration.py`
- **_offloader()** (4 connections) — `core/tests/test_cloud_integration.py`
- *... and 34 more nodes in this community*

## Relationships

- [Run State Rendering](Run_State_Rendering.md) (58 shared connections)
- [Run Definition Domain Model](Run_Definition_Domain_Model.md) (45 shared connections)
- [Result Tree Text Rendering](Result_Tree_Text_Rendering.md) (16 shared connections)
- [Conditional Write Tests](Conditional_Write_Tests.md) (9 shared connections)
- [Core Adapters Documentation](Core_Adapters_Documentation.md) (9 shared connections)
- [S3 Step Argument Offload](S3_Step_Argument_Offload.md) (7 shared connections)
- [Lambda Handler Event Tests](Lambda_Handler_Event_Tests.md) (5 shared connections)
- [Reconcile Tick and Report](Reconcile_Tick_and_Report.md) (5 shared connections)
- [Cloud Launcher and EventLog](Cloud_Launcher_and_EventLog.md) (4 shared connections)
- [Event Records Projection](Event_Records_Projection.md) (4 shared connections)
- [Wallclock Timestamp Source](Wallclock_Timestamp_Source.md) (4 shared connections)
- [CLI Command Entrypoints](CLI_Command_Entrypoints.md) (2 shared connections)

## Source Files

- `core/gherkai_core/adapters/run_store/ddb.py`
- `core/gherkai_core/model.py`
- `core/tests/test_cloud_integration.py`
- `core/tests/test_ddb_run_store.py`
- `core/tests/test_stores.py`

## Audit Trail

- EXTRACTED: 252 (88%)
- INFERRED: 36 (12%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*