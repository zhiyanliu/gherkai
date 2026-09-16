# Job Explain & S3 Offload

> 105 nodes · cohesion 0.04

## Key Concepts

- **Job** (134 connections) — `core/gherkai_core/model.py`
- **RunMeta** (119 connections) — `core/gherkai_core/model.py`
- **Scenario** (73 connections) — `core/gherkai_core/model.py`
- **Step** (72 connections) — `core/gherkai_core/model.py`
- **DynamoDBRunStore** (39 connections) — `core/gherkai_core/adapters/run_store/ddb.py`
- **StepArgument** (31 connections) — `core/gherkai_core/model.py`
- **S3StepArgumentOffloader** (27 connections) — `core/gherkai_core/adapters/run_store/arg_offload.py`
- **test_arg_offload.py** (23 connections) — `core/tests/test_arg_offload.py`
- **_timeout_built()** (18 connections) — `deploy_aws/tests/test_lambda_handlers.py`
- **_FakeSchedulerClient** (17 connections) — `deploy_aws/tests/test_lambda_handlers.py`
- **conftest.py** (14 connections) — `core/tests/conftest.py`
- **_seed_finished_run()** (13 connections) — `deploy_aws/tests/test_lambda_handlers.py`
- **BoomLauncher** (12 connections) — `core/tests/test_reconcile.py`
- **_OrderRecordingRunStore** (12 connections) — `core/tests/test_reconcile.py`
- **ConflictException** (12 connections) — `deploy_aws/tests/test_lambda_handlers.py`
- **exceptions** (12 connections) — `deploy_aws/tests/test_lambda_handlers.py`
- **test_report_still_written_when_the_run_duration_read_fails()** (12 connections) — `deploy_aws/tests/test_lambda_handlers.py`
- **test_explain_to_dict_drops_unmatched_scopes_and_keeps_job_fact()** (11 connections) — `cli/tests/test_main.py`
- **test_build_wires_arg_offloader_so_step_argument_bodies_read_back()** (11 connections) — `deploy_aws/tests/test_lambda_handlers.py`
- **build_cloud_stores()** (11 connections) — `runtime/gherkai_runtime/compose.py`
- **test_detached_flag_on_state_item()** (10 connections) — `core/tests/test_ddb_run_store.py`
- **test_worker_task_def_arns_on_state_item()** (10 connections) — `core/tests/test_ddb_run_store.py`
- **test_meta_json_holds_pointers_not_payload()** (9 connections) — `core/tests/test_arg_offload.py`
- **test_reader_without_offloader_fails_loud_on_offloaded_meta()** (9 connections) — `core/tests/test_arg_offload.py`
- **test_reader_without_offloader_not_fooled_by_content_ref_as_text()** (9 connections) — `core/tests/test_arg_offload.py`
- *... and 80 more nodes in this community*

## Relationships

- [DynamoDB RunStore Adapter](DynamoDB_RunStore_Adapter.md) (59 shared connections)
- [Cloud Boto3 Guards & EventLog](Cloud_Boto3_Guards_%26_EventLog.md) (48 shared connections)
- [Run State Rendering](Run_State_Rendering.md) (33 shared connections)
- [Reconciler Ports](Reconciler_Ports.md) (25 shared connections)
- [Cloud Job Launcher](Cloud_Job_Launcher.md) (20 shared connections)
- [Cloud Adapter Integration Tests](Cloud_Adapter_Integration_Tests.md) (19 shared connections)
- [Schedule Core & Fakes](Schedule_Core_%26_Fakes.md) (18 shared connections)
- [Text Render & Wording Guards](Text_Render_%26_Wording_Guards.md) (17 shared connections)
- [S3 Report Store & Control Plane](S3_Report_Store_%26_Control_Plane.md) (17 shared connections)
- [SQLite Event Log](SQLite_Event_Log.md) (16 shared connections)
- [Job Timeout Handling](Job_Timeout_Handling.md) (13 shared connections)
- [Run State Projection](Run_State_Projection.md) (13 shared connections)

## Source Files

- `cli/tests/test_main.py`
- `core/gherkai_core/adapters/run_store/arg_offload.py`
- `core/gherkai_core/adapters/run_store/ddb.py`
- `core/gherkai_core/model.py`
- `core/gherkai_core/serialize.py`
- `core/tests/conftest.py`
- `core/tests/test_arg_offload.py`
- `core/tests/test_ddb_run_store.py`
- `core/tests/test_project.py`
- `core/tests/test_reconcile.py`
- `core/tests/test_subprocess_engine.py`
- `core/tests/test_wire.py`
- `deploy_aws/tests/test_lambda_handlers.py`
- `runtime/gherkai_runtime/compose.py`

## Audit Trail

- EXTRACTED: 531 (76%)
- INFERRED: 172 (24%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*