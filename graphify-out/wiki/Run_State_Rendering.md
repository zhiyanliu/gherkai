# Run State Rendering

> 90 nodes · cohesion 0.04

## Key Concepts

- **RunState** (127 connections) — `core/gherkai_core/model.py`
- **test_stores.py** (56 connections) — `core/tests/test_stores.py`
- **LocalRunStore** (53 connections) — `core/gherkai_core/adapters/run_store/local.py`
- **_sample_run()** (39 connections) — `core/tests/test_stores.py`
- **run_store/local.py** (24 connections) — `core/gherkai_core/adapters/run_store/local.py`
- **run_store/ddb.py** (20 connections) — `core/gherkai_core/adapters/run_store/ddb.py`
- **run_meta_from_dict()** (16 connections) — `core/gherkai_core/serialize.py`
- **run_meta_to_dict()** (16 connections) — `core/gherkai_core/serialize.py`
- **run_state_from_result()** (10 connections) — `core/gherkai_core/model.py`
- **Path** (10 connections)
- **_mk_state()** (9 connections) — `cli/tests/test_main.py`
- **test_local_run_store_atomic.py** (9 connections) — `core/tests/test_local_run_store_atomic.py`
- **render_run_state()** (8 connections) — `cli/gherkai_cli/render.py`
- **.save_run()** (8 connections) — `core/gherkai_core/adapters/run_store/local.py`
- **._write_state()** (8 connections) — `core/gherkai_core/adapters/run_store/local.py`
- **test_explain_cloud_not_landed_hint_carries_cloud_locator_flags()** (7 connections) — `cli/tests/test_main.py`
- **.load_run_state()** (7 connections) — `core/gherkai_core/adapters/run_store/local.py`
- **._locked_rmw()** (7 connections) — `core/gherkai_core/adapters/run_store/local.py`
- **_lifecycle_rank()** (7 connections) — `core/gherkai_core/project.py`
- **test_render_status_pending_run_with_claimed_job_does_not_hint()** (6 connections) — `cli/tests/test_main.py`
- **_atomic_write_json()** (6 connections) — `core/gherkai_core/adapters/run_store/local.py`
- **.finalize_run()** (6 connections) — `core/gherkai_core/adapters/run_store/local.py`
- **.update_job_state()** (6 connections) — `core/gherkai_core/adapters/run_store/local.py`
- **run_state_from_dict()** (6 connections) — `core/gherkai_core/serialize.py`
- **run_state_to_dict()** (6 connections) — `core/gherkai_core/serialize.py`
- *... and 65 more nodes in this community*

## Relationships

- [DynamoDB Run Store](DynamoDB_Run_Store.md) (58 shared connections)
- [Run Definition Domain Model](Run_Definition_Domain_Model.md) (38 shared connections)
- [Result Tree Text Rendering](Result_Tree_Text_Rendering.md) (30 shared connections)
- [Result Store Serialization](Result_Store_Serialization.md) (29 shared connections)
- [Core Adapters Documentation](Core_Adapters_Documentation.md) (15 shared connections)
- [Conditional Write Tests](Conditional_Write_Tests.md) (12 shared connections)
- [Run Persistence Orchestration](Run_Persistence_Orchestration.md) (10 shared connections)
- [Reconcile Tick and Report](Reconcile_Tick_and_Report.md) (8 shared connections)
- [Wallclock Timestamp Source](Wallclock_Timestamp_Source.md) (8 shared connections)
- [S3 Result Store](S3_Result_Store.md) (8 shared connections)
- [Status Rendering & Exit Codes](Status_Rendering_%26_Exit_Codes.md) (7 shared connections)
- [Lambda Handler Event Tests](Lambda_Handler_Event_Tests.md) (7 shared connections)

## Source Files

- `cli/gherkai_cli/render.py`
- `cli/tests/test_main.py`
- `cli/tests/test_render.py`
- `core/gherkai_core/adapters/run_store/__init__.py`
- `core/gherkai_core/adapters/run_store/ddb.py`
- `core/gherkai_core/adapters/run_store/local.py`
- `core/gherkai_core/model.py`
- `core/gherkai_core/persist.py`
- `core/gherkai_core/ports.py`
- `core/gherkai_core/project.py`
- `core/gherkai_core/serialize.py`
- `core/tests/test_conditional_writes.py`
- `core/tests/test_ddb_run_store.py`
- `core/tests/test_local_run_store_atomic.py`
- `core/tests/test_stores.py`

## Audit Trail

- EXTRACTED: 429 (91%)
- INFERRED: 40 (9%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*