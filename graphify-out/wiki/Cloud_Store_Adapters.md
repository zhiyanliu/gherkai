# Cloud Store Adapters

> 89 nodes · cohesion 0.05

## Key Concepts

- **JobState** (101 connections) — `core/gherkai_core/model.py`
- **test_stores.py** (56 connections) — `core/tests/test_stores.py`
- **serialize.py** (44 connections) — `core/gherkai_core/serialize.py`
- **_sample_run()** (39 connections) — `core/tests/test_stores.py`
- **run_store/local.py** (24 connections) — `core/gherkai_core/adapters/run_store/local.py`
- **test_ddb_run_store.py** (24 connections) — `core/tests/test_ddb_run_store.py`
- **job_result_from_dict()** (22 connections) — `core/gherkai_core/serialize.py`
- **run_store/ddb.py** (20 connections) — `core/gherkai_core/adapters/run_store/ddb.py`
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
- **job_from_dict()** (8 connections) — `core/gherkai_core/serialize.py`
- **run_state_from_dict()** (6 connections) — `core/gherkai_core/serialize.py`
- **run_state_to_dict()** (6 connections) — `core/gherkai_core/serialize.py`
- **test_job_state_claimed_at_round_trip()** (6 connections) — `core/tests/test_stores.py`
- **test_realtime_write_lifecycle()** (6 connections) — `core/tests/test_stores.py`
- **test_run_state_jobs_map_round_trip()** (6 connections) — `core/tests/test_stores.py`
- *... and 64 more nodes in this community*

## Relationships

- [Job Domain Models](Job_Domain_Models.md) (54 shared connections)
- [Run Result Aggregation Tree](Run_Result_Aggregation_Tree.md) (36 shared connections)
- [Run State Store](Run_State_Store.md) (32 shared connections)
- [Run Store Adapters](Run_Store_Adapters.md) (18 shared connections)
- [Result Store & Report Refs](Result_Store_%26_Report_Refs.md) (16 shared connections)
- [S3 Store Adapters](S3_Store_Adapters.md) (13 shared connections)
- [Cloud Integration Tests](Cloud_Integration_Tests.md) (13 shared connections)
- [Local Result Store](Local_Result_Store.md) (12 shared connections)
- [Event Log Adapters](Event_Log_Adapters.md) (8 shared connections)
- [Boto Guard and Arg Offload](Boto_Guard_and_Arg_Offload.md) (7 shared connections)
- [Run State Projection](Run_State_Projection.md) (7 shared connections)
- [Reconciler Orchestration](Reconciler_Orchestration.md) (6 shared connections)

## Source Files

- `core/gherkai_core/adapters/result_store/local.py`
- `core/gherkai_core/adapters/result_store/s3.py`
- `core/gherkai_core/adapters/run_store/ddb.py`
- `core/gherkai_core/adapters/run_store/local.py`
- `core/gherkai_core/model.py`
- `core/gherkai_core/serialize.py`
- `core/tests/test_ddb_run_store.py`
- `core/tests/test_lifecycle_states.py`
- `core/tests/test_stores.py`

## Audit Trail

- EXTRACTED: 440 (94%)
- INFERRED: 28 (6%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*