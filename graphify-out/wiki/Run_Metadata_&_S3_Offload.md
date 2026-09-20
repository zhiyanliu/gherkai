# Run Metadata & S3 Offload

> 120 nodes · cohesion 0.04

## Key Concepts

- **Job** (134 connections) — `core/gherkai_core/model.py`
- **RunMeta** (119 connections) — `core/gherkai_core/model.py`
- **Scenario** (73 connections) — `core/gherkai_core/model.py`
- **Step** (72 connections) — `core/gherkai_core/model.py`
- **DynamoDBRunStore** (40 connections) — `core/gherkai_core/adapters/run_store/ddb.py`
- **StepArgument** (31 connections) — `core/gherkai_core/model.py`
- **S3StepArgumentOffloader** (27 connections) — `core/gherkai_core/adapters/run_store/arg_offload.py`
- **_FakeEcs** (25 connections) — `deploy_aws/tests/test_lambda_handlers.py`
- **test_ddb_run_store.py** (24 connections) — `core/tests/test_ddb_run_store.py`
- **test_arg_offload.py** (23 connections) — `core/tests/test_arg_offload.py`
- **_seed_run()** (23 connections) — `deploy_aws/tests/test_lambda_handlers.py`
- **_timeout_built()** (20 connections) — `deploy_aws/tests/test_lambda_handlers.py`
- **_FakeSchedulerClient** (17 connections) — `deploy_aws/tests/test_lambda_handlers.py`
- **core/tests/conftest.py** (14 connections) — `core/tests/conftest.py`
- **_seed_finished_run()** (13 connections) — `deploy_aws/tests/test_lambda_handlers.py`
- **BoomLauncher** (12 connections) — `core/tests/test_reconcile.py`
- **ConflictException** (12 connections) — `deploy_aws/tests/test_lambda_handlers.py`
- **exceptions** (12 connections) — `deploy_aws/tests/test_lambda_handlers.py`
- **test_report_still_written_when_the_run_duration_read_fails()** (12 connections) — `deploy_aws/tests/test_lambda_handlers.py`
- **_job()** (11 connections) — `core/tests/test_cloud_reconcile.py`
- **test_build_wires_arg_offloader_so_step_argument_bodies_read_back()** (11 connections) — `deploy_aws/tests/test_lambda_handlers.py`
- **build_cloud_stores()** (11 connections) — `runtime/gherkai_runtime/compose.py`
- **test_detached_flag_on_state_item()** (10 connections) — `core/tests/test_ddb_run_store.py`
- **test_worker_task_def_arns_on_state_item()** (10 connections) — `core/tests/test_ddb_run_store.py`
- **test_meta_json_holds_pointers_not_payload()** (9 connections) — `core/tests/test_arg_offload.py`
- *... and 95 more nodes in this community*

## Relationships

- [Run State Rendering](Run_State_Rendering.md) (75 shared connections)
- [Local & S3 Result Stores](Local_%26_S3_Result_Stores.md) (37 shared connections)
- [Reconcile Orchestration](Reconcile_Orchestration.md) (30 shared connections)
- [S3 Result Store Port](S3_Result_Store_Port.md) (26 shared connections)
- [Lambda Handler Tests](Lambda_Handler_Tests.md) (26 shared connections)
- [Event Log & Projection](Event_Log_%26_Projection.md) (22 shared connections)
- [Explain Rendering Tests](Explain_Rendering_Tests.md) (21 shared connections)
- [Cloud Adapter Integration Tests](Cloud_Adapter_Integration_Tests.md) (19 shared connections)
- [Cloud Launcher](Cloud_Launcher.md) (16 shared connections)
- [Run Scheduling Core](Run_Scheduling_Core.md) (14 shared connections)
- [Conditional Write Contract Tests](Conditional_Write_Contract_Tests.md) (12 shared connections)
- [Subprocess Engine Tests](Subprocess_Engine_Tests.md) (11 shared connections)

## Source Files

- `cli/tests/test_main.py`
- `core/gherkai_core/adapters/run_store/arg_offload.py`
- `core/gherkai_core/adapters/run_store/ddb.py`
- `core/gherkai_core/model.py`
- `core/tests/conftest.py`
- `core/tests/test_arg_offload.py`
- `core/tests/test_cloud_reconcile.py`
- `core/tests/test_ddb_run_store.py`
- `core/tests/test_project.py`
- `core/tests/test_reconcile.py`
- `core/tests/test_sqlite_event_log.py`
- `core/tests/test_subprocess_engine.py`
- `core/tests/test_wire.py`
- `deploy_aws/tests/test_lambda_handlers.py`
- `runtime/gherkai_runtime/compose.py`
- `runtime/tests/test_tunnel_host.py`

## Audit Trail

- EXTRACTED: 584 (77%)
- INFERRED: 173 (23%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*