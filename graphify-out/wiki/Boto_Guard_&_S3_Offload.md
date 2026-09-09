# Boto Guard & S3 Offload

> 58 nodes · cohesion 0.05

## Key Concepts

- **Status** (93 connections) — `core/gherkai_core/model.py`
- **DynamoDBRunStore** (37 connections) — `core/gherkai_core/adapters/run_store/ddb.py`
- **run_store/ddb.py** (20 connections) — `core/gherkai_core/adapters/run_store/ddb.py`
- **require_boto3()** (14 connections) — `core/gherkai_core/adapters/_boto.py`
- **projected_run_status()** (10 connections) — `core/gherkai_core/project.py`
- **_boto.py** (8 connections) — `core/gherkai_core/adapters/_boto.py`
- **.create_run()** (8 connections) — `core/gherkai_core/adapters/run_store/ddb.py`
- **arg_offload.py** (7 connections) — `core/gherkai_core/adapters/run_store/arg_offload.py`
- **_lifecycle_rank()** (7 connections) — `core/gherkai_core/project.py`
- **.project_state()** (6 connections) — `core/gherkai_core/adapters/run_store/ddb.py`
- **_job_state_to_item()** (6 connections) — `core/gherkai_core/adapters/run_store/ddb.py`
- **has_pointers()** (5 connections) — `core/gherkai_core/adapters/run_store/arg_offload.py`
- **_iter_arguments()** (5 connections) — `core/gherkai_core/adapters/run_store/arg_offload.py`
- **.load_run_meta()** (5 connections) — `core/gherkai_core/adapters/run_store/ddb.py`
- **.load_run_state()** (5 connections) — `core/gherkai_core/adapters/run_store/ddb.py`
- **.save_run()** (5 connections) — `core/gherkai_core/adapters/run_store/ddb.py`
- **.update_job_state()** (4 connections) — `core/gherkai_core/adapters/run_store/ddb.py`
- **_job_state_from_item()** (4 connections) — `core/gherkai_core/adapters/run_store/ddb.py`
- **_state_scalars()** (4 connections) — `core/gherkai_core/adapters/run_store/ddb.py`
- **test_projected_run_status_pending_only_while_all_jobs_pending()** (4 connections) — `core/tests/test_project.py`
- **.__init__()** (3 connections) — `core/gherkai_core/adapters/result_store/s3.py`
- **.finalize_run()** (3 connections) — `core/gherkai_core/adapters/run_store/ddb.py`
- **.__init__()** (3 connections) — `core/gherkai_core/adapters/run_store/ddb.py`
- **.try_finalize()** (3 connections) — `core/gherkai_core/adapters/run_store/ddb.py`
- **.try_finalize()** (3 connections) — `core/gherkai_core/ports.py`
- *... and 33 more nodes in this community*

## Relationships

- [Run Result Rendering](Run_Result_Rendering.md) (32 shared connections)
- [Run State Rendering](Run_State_Rendering.md) (30 shared connections)
- [Engine Ports & Adapters](Engine_Ports_%26_Adapters.md) (15 shared connections)
- [S3 Result Store](S3_Result_Store.md) (7 shared connections)
- [Worker Image Management](Worker_Image_Management.md) (6 shared connections)
- [Terminal Status Aggregation](Terminal_Status_Aggregation.md) (5 shared connections)
- [S3 Argument Offloader](S3_Argument_Offloader.md) (4 shared connections)
- [Cloud Launcher & DDB Event Log](Cloud_Launcher_%26_DDB_Event_Log.md) (4 shared connections)
- [Event Progress Formatting](Event_Progress_Formatting.md) (4 shared connections)
- [SQLite Event Log](SQLite_Event_Log.md) (4 shared connections)
- [Cloud Test Fixtures](Cloud_Test_Fixtures.md) (3 shared connections)
- [Local Result Store](Local_Result_Store.md) (3 shared connections)

## Source Files

- `core/gherkai_core/adapters/_boto.py`
- `core/gherkai_core/adapters/event_log/ddb.py`
- `core/gherkai_core/adapters/result_store/s3.py`
- `core/gherkai_core/adapters/run_store/arg_offload.py`
- `core/gherkai_core/adapters/run_store/ddb.py`
- `core/gherkai_core/model.py`
- `core/gherkai_core/ports.py`
- `core/gherkai_core/project.py`
- `core/tests/test_project.py`

## Audit Trail

- EXTRACTED: 182 (79%)
- INFERRED: 49 (21%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*