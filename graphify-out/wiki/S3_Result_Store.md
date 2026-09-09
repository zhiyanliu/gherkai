# S3 Result Store

> 52 nodes · cohesion 0.07

## Key Concepts

- **serialize.py** (43 connections) — `core/gherkai_core/serialize.py`
- **job_result_from_dict()** (21 connections) — `core/gherkai_core/serialize.py`
- **S3ResultStore** (18 connections) — `core/gherkai_core/adapters/result_store/s3.py`
- **test_s3_result_store.py** (15 connections) — `core/tests/test_s3_result_store.py`
- **job_result_to_dict()** (14 connections) — `core/gherkai_core/serialize.py`
- **_job_def()** (14 connections) — `core/tests/test_stores.py`
- **result_store/local.py** (9 connections) — `core/gherkai_core/adapters/result_store/local.py`
- **result_store/s3.py** (9 connections) — `core/gherkai_core/adapters/result_store/s3.py`
- **job_to_dict()** (9 connections) — `core/gherkai_core/serialize.py`
- **job_from_dict()** (8 connections) — `core/gherkai_core/serialize.py`
- **test_job_timeout_s_round_trip()** (6 connections) — `core/tests/test_stores.py`
- **.load_all()** (5 connections) — `core/gherkai_core/adapters/result_store/s3.py`
- **.load_job_result()** (5 connections) — `core/gherkai_core/adapters/result_store/s3.py`
- **.save_job_result()** (5 connections) — `core/gherkai_core/adapters/result_store/s3.py`
- **_scenario_def_from_dict()** (5 connections) — `core/gherkai_core/serialize.py`
- **_step_from_dict()** (5 connections) — `core/gherkai_core/serialize.py`
- **test_new_states_round_trip()** (5 connections) — `core/tests/test_lifecycle_states.py`
- **._key()** (4 connections) — `core/gherkai_core/adapters/result_store/s3.py`
- **_argument_from_dict()** (4 connections) — `core/gherkai_core/serialize.py`
- **_scenario_def_to_dict()** (4 connections) — `core/gherkai_core/serialize.py`
- **_step_to_dict()** (4 connections) — `core/gherkai_core/serialize.py`
- **test_prefix_isolates_runs()** (4 connections) — `core/tests/test_s3_result_store.py`
- **test_result_store_single_job_file_is_self_contained()** (4 connections) — `core/tests/test_stores.py`
- **._jobs_prefix()** (3 connections) — `core/gherkai_core/adapters/result_store/s3.py`
- **_argument_to_dict()** (3 connections) — `core/gherkai_core/serialize.py`
- *... and 27 more nodes in this community*

## Relationships

- [Run State Rendering](Run_State_Rendering.md) (30 shared connections)
- [Run Result Rendering](Run_Result_Rendering.md) (19 shared connections)
- [Engine Ports & Adapters](Engine_Ports_%26_Adapters.md) (18 shared connections)
- [Boto Guard & S3 Offload](Boto_Guard_%26_S3_Offload.md) (7 shared connections)
- [Report Refs & Results](Report_Refs_%26_Results.md) (7 shared connections)
- [Local Result Store](Local_Result_Store.md) (5 shared connections)
- [Terminal Status Aggregation](Terminal_Status_Aggregation.md) (4 shared connections)
- [Cloud Test Fixtures](Cloud_Test_Fixtures.md) (2 shared connections)
- [Event Progress Formatting](Event_Progress_Formatting.md) (2 shared connections)
- [Reconciler Lambda](Reconciler_Lambda.md) (1 shared connections)
- [Cloud Store Composition](Cloud_Store_Composition.md) (1 shared connections)
- [Plan Rendering & Output](Plan_Rendering_%26_Output.md) (1 shared connections)

## Source Files

- `core/gherkai_core/adapters/result_store/local.py`
- `core/gherkai_core/adapters/result_store/s3.py`
- `core/gherkai_core/serialize.py`
- `core/tests/test_lifecycle_states.py`
- `core/tests/test_s3_result_store.py`
- `core/tests/test_stores.py`

## Audit Trail

- EXTRACTED: 183 (98%)
- INFERRED: 3 (2%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*