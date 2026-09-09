# Run State Rendering

> 90 nodes · cohesion 0.05

## Key Concepts

- **RunState** (104 connections) — `core/gherkai_core/model.py`
- **JobState** (85 connections) — `core/gherkai_core/model.py`
- **test_stores.py** (55 connections) — `core/tests/test_stores.py`
- **_sample_run()** (38 connections) — `core/tests/test_stores.py`
- **test_cloud_integration.py** (28 connections) — `core/tests/test_cloud_integration.py`
- **test_ddb_run_store.py** (24 connections) — `core/tests/test_ddb_run_store.py`
- **run_store/local.py** (20 connections) — `core/gherkai_core/adapters/run_store/local.py`
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
- **.load_run_state()** (7 connections) — `core/gherkai_core/adapters/run_store/local.py`
- **.save_run()** (7 connections) — `core/gherkai_core/adapters/run_store/local.py`
- **._write_state()** (7 connections) — `core/gherkai_core/adapters/run_store/local.py`
- **test_ddb_empty_string_scalar_and_map_entry_real()** (7 connections) — `core/tests/test_cloud_integration.py`
- **test_ddb_run_store_lifecycle_real()** (7 connections) — `core/tests/test_cloud_integration.py`
- **test_ddb_session_id_none_omitted_real()** (7 connections) — `core/tests/test_cloud_integration.py`
- **render_run_state()** (6 connections) — `cli/gherkai_cli/render.py`
- **.finalize_run()** (6 connections) — `core/gherkai_core/adapters/run_store/local.py`
- *... and 65 more nodes in this community*

## Relationships

- [Engine Ports & Adapters](Engine_Ports_%26_Adapters.md) (56 shared connections)
- [Run Result Rendering](Run_Result_Rendering.md) (54 shared connections)
- [Local Run Store](Local_Run_Store.md) (35 shared connections)
- [Boto Guard & S3 Offload](Boto_Guard_%26_S3_Offload.md) (30 shared connections)
- [S3 Result Store](S3_Result_Store.md) (30 shared connections)
- [Conditional Write Tests](Conditional_Write_Tests.md) (13 shared connections)
- [SQLite Event Log](SQLite_Event_Log.md) (9 shared connections)
- [Local Result Store](Local_Result_Store.md) (8 shared connections)
- [Cloud Launcher & DDB Event Log](Cloud_Launcher_%26_DDB_Event_Log.md) (8 shared connections)
- [Report Refs & Results](Report_Refs_%26_Results.md) (6 shared connections)
- [Status Render & Exit Codes](Status_Render_%26_Exit_Codes.md) (4 shared connections)
- [Event Replay Projection](Event_Replay_Projection.md) (4 shared connections)

## Source Files

- `cli/gherkai_cli/render.py`
- `cli/tests/test_render.py`
- `core/gherkai_core/adapters/run_store/local.py`
- `core/gherkai_core/model.py`
- `core/gherkai_core/persist.py`
- `core/gherkai_core/ports.py`
- `core/gherkai_core/serialize.py`
- `core/tests/test_cloud_integration.py`
- `core/tests/test_ddb_run_store.py`
- `core/tests/test_stores.py`

## Audit Trail

- EXTRACTED: 440 (90%)
- INFERRED: 47 (10%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*