# S3 Result Store

> 66 nodes · cohesion 0.05

## Key Concepts

- **JobResult** (84 connections) — `core/gherkai_core/model.py`
- **serialize.py** (45 connections) — `core/gherkai_core/serialize.py`
- **job_result_from_dict()** (22 connections) — `core/gherkai_core/serialize.py`
- **S3ResultStore** (17 connections) — `core/gherkai_core/adapters/result_store/s3.py`
- **job_result_to_dict()** (15 connections) — `core/gherkai_core/serialize.py`
- **test_s3_result_store.py** (15 connections) — `core/tests/test_s3_result_store.py`
- **_job_def()** (14 connections) — `core/tests/test_stores.py`
- **result_store/s3.py** (9 connections) — `core/gherkai_core/adapters/result_store/s3.py`
- **job_to_dict()** (9 connections) — `core/gherkai_core/serialize.py`
- **job_from_dict()** (8 connections) — `core/gherkai_core/serialize.py`
- **test_job_timeout_s_round_trip()** (6 connections) — `core/tests/test_stores.py`
- **test_step_message_survives_round_trip_and_missing_key_is_none()** (6 connections) — `core/tests/test_stores.py`
- **.load_all()** (5 connections) — `core/gherkai_core/adapters/result_store/s3.py`
- **.load_job_result()** (5 connections) — `core/gherkai_core/adapters/result_store/s3.py`
- **.save_job_result()** (5 connections) — `core/gherkai_core/adapters/result_store/s3.py`
- **.on_job_complete()** (5 connections) — `core/gherkai_core/persist.py`
- **_scenario_def_from_dict()** (5 connections) — `core/gherkai_core/serialize.py`
- **_step_from_dict()** (5 connections) — `core/gherkai_core/serialize.py`
- **test_new_states_round_trip()** (5 connections) — `core/tests/test_lifecycle_states.py`
- **.load_all()** (4 connections) — `core/gherkai_core/adapters/result_store/local.py`
- **.load_job_result()** (4 connections) — `core/gherkai_core/adapters/result_store/local.py`
- **._key()** (4 connections) — `core/gherkai_core/adapters/result_store/s3.py`
- **_argument_from_dict()** (4 connections) — `core/gherkai_core/serialize.py`
- **_scenario_def_to_dict()** (4 connections) — `core/gherkai_core/serialize.py`
- **_step_to_dict()** (4 connections) — `core/gherkai_core/serialize.py`
- *... and 41 more nodes in this community*

## Relationships

- [Cloud Launcher & Fargate Adapters](Cloud_Launcher_%26_Fargate_Adapters.md) (34 shared connections)
- [Job State Serialization](Job_State_Serialization.md) (31 shared connections)
- [Result Rendering & Explain](Result_Rendering_%26_Explain.md) (16 shared connections)
- [Job/Scenario Explain Model](Job-Scenario_Explain_Model.md) (15 shared connections)
- [Local Result Store & Persistence](Local_Result_Store_%26_Persistence.md) (7 shared connections)
- [Severity Aggregation & Fake Engine](Severity_Aggregation_%26_Fake_Engine.md) (7 shared connections)
- [Local Result Store](Local_Result_Store.md) (6 shared connections)
- [Fake DDB Table & SQLite Records](Fake_DDB_Table_%26_SQLite_Records.md) (5 shared connections)
- [Local Report Store](Local_Report_Store.md) (5 shared connections)
- [Boto3 Guard & Arg Offload](Boto3_Guard_%26_Arg_Offload.md) (3 shared connections)
- [Test Fixtures & Conftest](Test_Fixtures_%26_Conftest.md) (3 shared connections)
- [Explain JSON & Redaction](Explain_JSON_%26_Redaction.md) (3 shared connections)

## Source Files

- `core/gherkai_core/adapters/result_store/local.py`
- `core/gherkai_core/adapters/result_store/s3.py`
- `core/gherkai_core/model.py`
- `core/gherkai_core/persist.py`
- `core/gherkai_core/ports.py`
- `core/gherkai_core/serialize.py`
- `core/tests/conftest.py`
- `core/tests/test_lifecycle_states.py`
- `core/tests/test_s3_result_store.py`
- `core/tests/test_stores.py`

## Audit Trail

- EXTRACTED: 245 (91%)
- INFERRED: 25 (9%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*