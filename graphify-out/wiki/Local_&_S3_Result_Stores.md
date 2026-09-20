# Local & S3 Result Stores

> 100 nodes · cohesion 0.04

## Key Concepts

- **test_stores.py** (56 connections) — `core/tests/test_stores.py`
- **LocalRunStore** (53 connections) — `core/gherkai_core/adapters/run_store/local.py`
- **serialize.py** (43 connections) — `core/gherkai_core/serialize.py`
- **_sample_run()** (39 connections) — `core/tests/test_stores.py`
- **job_result_from_dict()** (22 connections) — `core/gherkai_core/serialize.py`
- **run_meta_from_dict()** (16 connections) — `core/gherkai_core/serialize.py`
- **run_meta_to_dict()** (16 connections) — `core/gherkai_core/serialize.py`
- **job_result_to_dict()** (15 connections) — `core/gherkai_core/serialize.py`
- **result_store/local.py** (12 connections) — `core/gherkai_core/adapters/result_store/local.py`
- **run_state_from_result()** (10 connections) — `core/gherkai_core/model.py`
- **from_dict()** (10 connections) — `core/gherkai_core/serialize.py`
- **Path** (10 connections)
- **result_store/s3.py** (9 connections) — `core/gherkai_core/adapters/result_store/s3.py`
- **job_to_dict()** (9 connections) — `core/gherkai_core/serialize.py`
- **to_dict()** (9 connections) — `core/gherkai_core/serialize.py`
- **_initial_state()** (9 connections) — `core/tests/test_stores.py`
- **.save_run()** (8 connections) — `core/gherkai_core/adapters/run_store/local.py`
- **._write_state()** (8 connections) — `core/gherkai_core/adapters/run_store/local.py`
- **job_from_dict()** (8 connections) — `core/gherkai_core/serialize.py`
- **.load_run_state()** (7 connections) — `core/gherkai_core/adapters/run_store/local.py`
- **._locked_rmw()** (7 connections) — `core/gherkai_core/adapters/run_store/local.py`
- **_atomic_write_json()** (6 connections) — `core/gherkai_core/adapters/run_store/local.py`
- **.finalize_run()** (6 connections) — `core/gherkai_core/adapters/run_store/local.py`
- **.update_job_state()** (6 connections) — `core/gherkai_core/adapters/run_store/local.py`
- **run_state_to_dict()** (6 connections) — `core/gherkai_core/serialize.py`
- *... and 75 more nodes in this community*

## Relationships

- [Run State Rendering](Run_State_Rendering.md) (56 shared connections)
- [Run Metadata & S3 Offload](Run_Metadata_%26_S3_Offload.md) (37 shared connections)
- [S3 Result Store Port](S3_Result_Store_Port.md) (21 shared connections)
- [Explain Rendering Tests](Explain_Rendering_Tests.md) (15 shared connections)
- [Local Result Store](Local_Result_Store.md) (12 shared connections)
- [Cloud Adapter Integration Tests](Cloud_Adapter_Integration_Tests.md) (7 shared connections)
- [Local Reconcile Rebuild](Local_Reconcile_Rebuild.md) (5 shared connections)
- [Local Report Store](Local_Report_Store.md) (5 shared connections)
- [Event Progress Formatting](Event_Progress_Formatting.md) (4 shared connections)
- [Core Typed Errors](Core_Typed_Errors.md) (4 shared connections)
- [Atomic File Writes](Atomic_File_Writes.md) (3 shared connections)
- [Reconcile Orchestration](Reconcile_Orchestration.md) (3 shared connections)

## Source Files

- `core/gherkai_core/adapters/result_store/local.py`
- `core/gherkai_core/adapters/result_store/s3.py`
- `core/gherkai_core/adapters/run_store/local.py`
- `core/gherkai_core/model.py`
- `core/gherkai_core/serialize.py`
- `core/tests/test_ddb_run_store.py`
- `core/tests/test_lifecycle_states.py`
- `core/tests/test_stores.py`

## Audit Trail

- EXTRACTED: 395 (98%)
- INFERRED: 7 (2%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*