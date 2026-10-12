# Job/Scenario Explain Model

> 111 nodes · cohesion 0.04

## Key Concepts

- **Job** (135 connections) — `core/gherkai_core/model.py`
- **Scenario** (73 connections) — `core/gherkai_core/model.py`
- **Step** (72 connections) — `core/gherkai_core/model.py`
- **DynamoDBRunStore** (40 connections) — `core/gherkai_core/adapters/run_store/ddb.py`
- **wire.py** (38 connections) — `core/gherkai_core/wire.py`
- **StepArgument** (31 connections) — `core/gherkai_core/model.py`
- **S3StepArgumentOffloader** (27 connections) — `core/gherkai_core/adapters/run_store/arg_offload.py`
- **WorkerNetworkError** (26 connections) — `core/gherkai_core/errors.py`
- **test_arg_offload.py** (23 connections) — `core/tests/test_arg_offload.py`
- **_MissingThenStoppedEcs** (17 connections) — `core/tests/test_fargate_engine.py`
- **_FakeSchedulerClient** (17 connections) — `deploy_aws/tests/test_lambda_handlers.py`
- **_FakeEcs** (15 connections) — `core/tests/test_fargate_engine.py`
- **_SeqEcs** (15 connections) — `core/tests/test_fargate_engine.py`
- **_FakeProc** (15 connections) — `runtime/tests/test_tunnel.py`
- **FargateWorkerHandle** (12 connections) — `core/gherkai_core/adapters/fargate_engine.py`
- **raise_for_worker_exit()** (12 connections) — `core/gherkai_core/wire.py`
- **test_offload_unblocks_oversized_docstring_real()** (12 connections) — `core/tests/test_cloud_integration.py`
- **BoomLauncher** (12 connections) — `core/tests/test_reconcile.py`
- **_OrderRecordingRunStore** (12 connections) — `core/tests/test_reconcile.py`
- **ConflictException** (12 connections) — `deploy_aws/tests/test_lambda_handlers.py`
- **exceptions** (12 connections) — `deploy_aws/tests/test_lambda_handlers.py`
- **test_report_still_written_when_the_run_duration_read_fails()** (12 connections) — `deploy_aws/tests/test_lambda_handlers.py`
- **test_explain_to_dict_drops_unmatched_scopes_and_keeps_job_fact()** (11 connections) — `cli/tests/test_main.py`
- **test_offload_round_trip_real()** (11 connections) — `core/tests/test_cloud_integration.py`
- **test_build_wires_arg_offloader_so_step_argument_bodies_read_back()** (11 connections) — `deploy_aws/tests/test_lambda_handlers.py`
- *... and 86 more nodes in this community*

## Relationships

- [Cloud Launcher & Fargate Adapters](Cloud_Launcher_%26_Fargate_Adapters.md) (85 shared connections)
- [Job State Serialization](Job_State_Serialization.md) (41 shared connections)
- [Run State Rendering & DDB Store](Run_State_Rendering_%26_DDB_Store.md) (33 shared connections)
- [Lambda Handler Event Parsing Tests](Lambda_Handler_Event_Parsing_Tests.md) (22 shared connections)
- [Event Progress Formatting](Event_Progress_Formatting.md) (18 shared connections)
- [Reconcile Tick & Report Finalize](Reconcile_Tick_%26_Report_Finalize.md) (16 shared connections)
- [S3 Result Store](S3_Result_Store.md) (15 shared connections)
- [Wire Protocol Serialization](Wire_Protocol_Serialization.md) (15 shared connections)
- [Feature Parsing & Errors](Feature_Parsing_%26_Errors.md) (14 shared connections)
- [Schedule Module Tests](Schedule_Module_Tests.md) (14 shared connections)
- [Fake DDB Table & SQLite Records](Fake_DDB_Table_%26_SQLite_Records.md) (14 shared connections)
- [Cloud Reconcile Launcher Tests](Cloud_Reconcile_Launcher_Tests.md) (13 shared connections)

## Source Files

- `cli/tests/test_main.py`
- `core/gherkai_core/adapters/fargate_engine.py`
- `core/gherkai_core/adapters/run_store/arg_offload.py`
- `core/gherkai_core/adapters/run_store/ddb.py`
- `core/gherkai_core/errors.py`
- `core/gherkai_core/model.py`
- `core/gherkai_core/wire.py`
- `core/tests/test_arg_offload.py`
- `core/tests/test_cloud_integration.py`
- `core/tests/test_ddb_run_store.py`
- `core/tests/test_fargate_engine.py`
- `core/tests/test_project.py`
- `core/tests/test_reconcile.py`
- `core/tests/test_subprocess_engine.py`
- `core/tests/test_wire.py`
- `deploy_aws/tests/test_lambda_handlers.py`
- `runtime/gherkai_runtime/compose.py`
- `runtime/tests/test_tunnel.py`
- `runtime/tests/test_tunnel_host.py`

## Audit Trail

- EXTRACTED: 499 (73%)
- INFERRED: 184 (27%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*