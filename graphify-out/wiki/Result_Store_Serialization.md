# Result Store Serialization

> 42 nodes · cohesion 0.08

## Key Concepts

- **serialize.py** (45 connections) — `core/gherkai_core/serialize.py`
- **job_result_from_dict()** (22 connections) — `core/gherkai_core/serialize.py`
- **job_result_to_dict()** (15 connections) — `core/gherkai_core/serialize.py`
- **result_store/local.py** (12 connections) — `core/gherkai_core/adapters/result_store/local.py`
- **from_dict()** (10 connections) — `core/gherkai_core/serialize.py`
- **result_store/s3.py** (9 connections) — `core/gherkai_core/adapters/result_store/s3.py`
- **job_to_dict()** (9 connections) — `core/gherkai_core/serialize.py`
- **to_dict()** (9 connections) — `core/gherkai_core/serialize.py`
- **job_from_dict()** (8 connections) — `core/gherkai_core/serialize.py`
- **test_step_message_survives_round_trip_and_missing_key_is_none()** (6 connections) — `core/tests/test_stores.py`
- **ref_to_dict()** (5 connections) — `core/gherkai_core/serialize.py`
- **_scenario_def_from_dict()** (5 connections) — `core/gherkai_core/serialize.py`
- **_step_from_dict()** (5 connections) — `core/gherkai_core/serialize.py`
- **test_new_states_round_trip()** (5 connections) — `core/tests/test_lifecycle_states.py`
- **.load_all()** (4 connections) — `core/gherkai_core/adapters/result_store/local.py`
- **.load_job_result()** (4 connections) — `core/gherkai_core/adapters/result_store/local.py`
- **_argument_from_dict()** (4 connections) — `core/gherkai_core/serialize.py`
- **_scenario_def_to_dict()** (4 connections) — `core/gherkai_core/serialize.py`
- **_step_to_dict()** (4 connections) — `core/gherkai_core/serialize.py`
- **test_aggregate_to_dict_normalized_no_def_duplication()** (4 connections) — `core/tests/test_stores.py`
- **test_result_store_single_job_file_is_self_contained()** (4 connections) — `core/tests/test_stores.py`
- **test_serialize_round_trip()** (4 connections) — `core/tests/test_stores.py`
- **test_serialize_round_trip_deep_equal_dict()** (4 connections) — `core/tests/test_stores.py`
- **_argument_to_dict()** (3 connections) — `core/gherkai_core/serialize.py`
- **Job** (3 connections)
- *... and 17 more nodes in this community*

## Relationships

- [Run State Rendering](Run_State_Rendering.md) (29 shared connections)
- [Result Tree Text Rendering](Result_Tree_Text_Rendering.md) (19 shared connections)
- [Run Definition Domain Model](Run_Definition_Domain_Model.md) (10 shared connections)
- [S3 Result Store](S3_Result_Store.md) (6 shared connections)
- [Worker Log Event Formatting](Worker_Log_Event_Formatting.md) (6 shared connections)
- [Run Persistence Orchestration](Run_Persistence_Orchestration.md) (5 shared connections)
- [Core Adapters Documentation](Core_Adapters_Documentation.md) (5 shared connections)
- [Atomic Local Writes](Atomic_Local_Writes.md) (3 shared connections)
- [Report Store Adapters](Report_Store_Adapters.md) (3 shared connections)
- [Boto3 Adapter Guard](Boto3_Adapter_Guard.md) (2 shared connections)
- [Explain Tree Rendering](Explain_Tree_Rendering.md) (2 shared connections)
- [DynamoDB Run Store](DynamoDB_Run_Store.md) (1 shared connections)

## Source Files

- `core/gherkai_core/adapters/result_store/local.py`
- `core/gherkai_core/adapters/result_store/s3.py`
- `core/gherkai_core/serialize.py`
- `core/tests/test_lifecycle_states.py`
- `core/tests/test_stores.py`

## Audit Trail

- EXTRACTED: 162 (100%)
- INFERRED: 0 (0%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*