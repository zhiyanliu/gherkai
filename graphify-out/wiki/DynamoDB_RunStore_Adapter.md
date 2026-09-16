# DynamoDB RunStore Adapter

> 102 nodes · cohesion 0.05

## Key Concepts

- **JobState** (100 connections) — `core/gherkai_core/model.py`
- **test_stores.py** (56 connections) — `core/tests/test_stores.py`
- **LocalRunStore** (53 connections) — `core/gherkai_core/adapters/run_store/local.py`
- **serialize.py** (43 connections) — `core/gherkai_core/serialize.py`
- **_sample_run()** (39 connections) — `core/tests/test_stores.py`
- **run_store/local.py** (24 connections) — `core/gherkai_core/adapters/run_store/local.py`
- **test_ddb_run_store.py** (24 connections) — `core/tests/test_ddb_run_store.py`
- **run_store/ddb.py** (20 connections) — `core/gherkai_core/adapters/run_store/ddb.py`
- **run_meta_from_dict()** (16 connections) — `core/gherkai_core/serialize.py`
- **run_meta_to_dict()** (16 connections) — `core/gherkai_core/serialize.py`
- **job_result_to_dict()** (15 connections) — `core/gherkai_core/serialize.py`
- **run_state_from_result()** (10 connections) — `core/gherkai_core/model.py`
- **from_dict()** (10 connections) — `core/gherkai_core/serialize.py`
- **Path** (10 connections)
- **job_to_dict()** (9 connections) — `core/gherkai_core/serialize.py`
- **to_dict()** (9 connections) — `core/gherkai_core/serialize.py`
- **test_local_run_store_atomic.py** (9 connections) — `core/tests/test_local_run_store_atomic.py`
- **_initial_state()** (9 connections) — `core/tests/test_stores.py`
- **.save_run()** (8 connections) — `core/gherkai_core/adapters/run_store/local.py`
- **._write_state()** (8 connections) — `core/gherkai_core/adapters/run_store/local.py`
- **.load_run_state()** (7 connections) — `core/gherkai_core/adapters/run_store/local.py`
- **._locked_rmw()** (7 connections) — `core/gherkai_core/adapters/run_store/local.py`
- **_atomic_write_json()** (6 connections) — `core/gherkai_core/adapters/run_store/local.py`
- **.finalize_run()** (6 connections) — `core/gherkai_core/adapters/run_store/local.py`
- **.update_job_state()** (6 connections) — `core/gherkai_core/adapters/run_store/local.py`
- *... and 77 more nodes in this community*

## Relationships

- [Job Explain & S3 Offload](Job_Explain_%26_S3_Offload.md) (59 shared connections)
- [Run State Rendering](Run_State_Rendering.md) (32 shared connections)
- [Cloud Boto3 Guards & EventLog](Cloud_Boto3_Guards_%26_EventLog.md) (31 shared connections)
- [S3 Result Store](S3_Result_Store.md) (24 shared connections)
- [SQLite Event Log](SQLite_Event_Log.md) (17 shared connections)
- [Cloud Adapter Integration Tests](Cloud_Adapter_Integration_Tests.md) (13 shared connections)
- [Local Result Store & Persistence](Local_Result_Store_%26_Persistence.md) (11 shared connections)
- [Text Render & Wording Guards](Text_Render_%26_Wording_Guards.md) (9 shared connections)
- [Run State Projection](Run_State_Projection.md) (8 shared connections)
- [Reconciler Ports](Reconciler_Ports.md) (8 shared connections)
- [Conditional Write Tests](Conditional_Write_Tests.md) (8 shared connections)
- [Local Report Store](Local_Report_Store.md) (8 shared connections)

## Source Files

- `core/gherkai_core/adapters/run_store/__init__.py`
- `core/gherkai_core/adapters/run_store/ddb.py`
- `core/gherkai_core/adapters/run_store/local.py`
- `core/gherkai_core/model.py`
- `core/gherkai_core/serialize.py`
- `core/tests/test_ddb_run_store.py`
- `core/tests/test_local_run_store_atomic.py`
- `core/tests/test_stores.py`

## Audit Trail

- EXTRACTED: 468 (94%)
- INFERRED: 32 (6%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*