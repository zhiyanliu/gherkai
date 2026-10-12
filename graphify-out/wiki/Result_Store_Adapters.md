# Result Store Adapters

> 35 nodes · cohesion 0.09

## Key Concepts

- **serialize.py** (45 connections) — `core/gherkai_core/serialize.py`
- **job_result_from_dict()** (22 connections) — `core/gherkai_core/serialize.py`
- **job_result_to_dict()** (15 connections) — `core/gherkai_core/serialize.py`
- **result_store/local.py** (12 connections) — `core/gherkai_core/adapters/result_store/local.py`
- **result_store/s3.py** (9 connections) — `core/gherkai_core/adapters/result_store/s3.py`
- **job_to_dict()** (9 connections) — `core/gherkai_core/serialize.py`
- **job_from_dict()** (8 connections) — `core/gherkai_core/serialize.py`
- **ref_to_dict()** (5 connections) — `core/gherkai_core/serialize.py`
- **_scenario_def_from_dict()** (5 connections) — `core/gherkai_core/serialize.py`
- **_step_from_dict()** (5 connections) — `core/gherkai_core/serialize.py`
- **test_new_states_round_trip()** (5 connections) — `core/tests/test_lifecycle_states.py`
- **.load_all()** (4 connections) — `core/gherkai_core/adapters/result_store/local.py`
- **.load_job_result()** (4 connections) — `core/gherkai_core/adapters/result_store/local.py`
- **_argument_from_dict()** (4 connections) — `core/gherkai_core/serialize.py`
- **_scenario_def_to_dict()** (4 connections) — `core/gherkai_core/serialize.py`
- **_step_to_dict()** (4 connections) — `core/gherkai_core/serialize.py`
- **test_result_store_single_job_file_is_self_contained()** (4 connections) — `core/tests/test_stores.py`
- **result_store/__init__.py** (3 connections) — `core/gherkai_core/adapters/result_store/__init__.py`
- **_argument_to_dict()** (3 connections) — `core/gherkai_core/serialize.py`
- **Job** (3 connections)
- **_ref_from_dict()** (3 connections) — `core/gherkai_core/serialize.py`
- **_votes_from_dict()** (3 connections) — `core/gherkai_core/serialize.py`
- **Scenario** (2 connections)
- **Step** (2 connections)
- **StepArgument** (2 connections)
- *... and 10 more nodes in this community*

## Relationships

- [DynamoDB Job State Store](DynamoDB_Job_State_Store.md) (20 shared connections)
- [S3 Result Store](S3_Result_Store.md) (14 shared connections)
- [Job Explain Data Model](Job_Explain_Data_Model.md) (10 shared connections)
- [Cloud Adapter Boundary Modules](Cloud_Adapter_Boundary_Modules.md) (7 shared connections)
- [Explain Reads And Report Store](Explain_Reads_And_Report_Store.md) (7 shared connections)
- [Run Persistence Local Stores](Run_Persistence_Local_Stores.md) (5 shared connections)
- [Run State Store](Run_State_Store.md) (4 shared connections)
- [Terminal State Aggregation](Terminal_State_Aggregation.md) (4 shared connections)
- [Atomic Local Writes](Atomic_Local_Writes.md) (3 shared connections)
- [Run Scheduling Events Core](Run_Scheduling_Events_Core.md) (2 shared connections)
- [Plan Explain Rendering](Plan_Explain_Rendering.md) (2 shared connections)
- [boto3 Client Injection](boto3_Client_Injection.md) (1 shared connections)

## Source Files

- `core/gherkai_core/adapters/result_store/__init__.py`
- `core/gherkai_core/adapters/result_store/local.py`
- `core/gherkai_core/adapters/result_store/s3.py`
- `core/gherkai_core/serialize.py`
- `core/tests/test_lifecycle_states.py`
- `core/tests/test_stores.py`

## Audit Trail

- EXTRACTED: 139 (100%)
- INFERRED: 0 (0%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*