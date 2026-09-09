# ResultStore Local/S3

> 34 nodes · cohesion 0.10

## Key Concepts

- **serialize.py** (43 connections) — `core/gherkai_core/serialize.py`
- **job_result_from_dict()** (21 connections) — `core/gherkai_core/serialize.py`
- **job_result_to_dict()** (14 connections) — `core/gherkai_core/serialize.py`
- **result_store/local.py** (9 connections) — `core/gherkai_core/adapters/result_store/local.py`
- **result_store/s3.py** (9 connections) — `core/gherkai_core/adapters/result_store/s3.py`
- **job_to_dict()** (9 connections) — `core/gherkai_core/serialize.py`
- **job_from_dict()** (8 connections) — `core/gherkai_core/serialize.py`
- **_scenario_def_from_dict()** (5 connections) — `core/gherkai_core/serialize.py`
- **_step_from_dict()** (5 connections) — `core/gherkai_core/serialize.py`
- **test_new_states_round_trip()** (5 connections) — `core/tests/test_lifecycle_states.py`
- **.load_all()** (4 connections) — `core/gherkai_core/adapters/result_store/local.py`
- **.load_job_result()** (4 connections) — `core/gherkai_core/adapters/result_store/local.py`
- **.save_job_result()** (4 connections) — `core/gherkai_core/adapters/result_store/local.py`
- **_argument_from_dict()** (4 connections) — `core/gherkai_core/serialize.py`
- **_scenario_def_to_dict()** (4 connections) — `core/gherkai_core/serialize.py`
- **_step_to_dict()** (4 connections) — `core/gherkai_core/serialize.py`
- **test_result_store_single_job_file_is_self_contained()** (4 connections) — `core/tests/test_stores.py`
- **_argument_to_dict()** (3 connections) — `core/gherkai_core/serialize.py`
- **Job** (3 connections)
- **_ref_from_dict()** (3 connections) — `core/gherkai_core/serialize.py`
- **_ref_to_dict()** (3 connections) — `core/gherkai_core/serialize.py`
- **_votes_from_dict()** (3 connections) — `core/gherkai_core/serialize.py`
- **Scenario** (2 connections)
- **Step** (2 connections)
- **StepArgument** (2 connections)
- *... and 9 more nodes in this community*

## Relationships

- [Run Result Verdict Model](Run_Result_Verdict_Model.md) (14 shared connections)
- [Engine Ports & Adapters](Engine_Ports_%26_Adapters.md) (13 shared connections)
- [DynamoDB RunStore Conditional Writes](DynamoDB_RunStore_Conditional_Writes.md) (13 shared connections)
- [Run State Rendering & Boto Guard](Run_State_Rendering_%26_Boto_Guard.md) (12 shared connections)
- [Render & ReportStore Local](Render_%26_ReportStore_Local.md) (7 shared connections)
- [Run Persistence Orchestration](Run_Persistence_Orchestration.md) (5 shared connections)
- [S3 ResultStore](S3_ResultStore.md) (4 shared connections)
- [Terminal Status Aggregation](Terminal_Status_Aggregation.md) (4 shared connections)
- [Event Formatting & Cost Model](Event_Formatting_%26_Cost_Model.md) (2 shared connections)
- [Plan Command & Rendering](Plan_Command_%26_Rendering.md) (2 shared connections)

## Source Files

- `core/gherkai_core/adapters/result_store/local.py`
- `core/gherkai_core/adapters/result_store/s3.py`
- `core/gherkai_core/serialize.py`
- `core/tests/test_lifecycle_states.py`
- `core/tests/test_stores.py`

## Audit Trail

- EXTRACTED: 131 (100%)
- INFERRED: 0 (0%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*