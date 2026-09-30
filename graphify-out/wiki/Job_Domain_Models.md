# Job Domain Models

> 80 nodes · cohesion 0.06

## Key Concepts

- **Job** (135 connections) — `core/gherkai_core/model.py`
- **RunMeta** (120 connections) — `core/gherkai_core/model.py`
- **model.py** (79 connections) — `core/gherkai_core/model.py`
- **Scenario** (73 connections) — `core/gherkai_core/model.py`
- **Step** (72 connections) — `core/gherkai_core/model.py`
- **StepArgument** (31 connections) — `core/gherkai_core/model.py`
- **test_arg_offload.py** (23 connections) — `core/tests/test_arg_offload.py`
- **_seed_run()** (23 connections) — `deploy_aws/tests/test_lambda_handlers.py`
- **fargate_engine.py** (21 connections) — `core/gherkai_core/adapters/fargate_engine.py`
- **_timeout_built()** (20 connections) — `deploy_aws/tests/test_lambda_handlers.py`
- **subprocess_engine.py** (19 connections) — `core/gherkai_core/adapters/subprocess_engine.py`
- **_FakeSchedulerClient** (17 connections) — `deploy_aws/tests/test_lambda_handlers.py`
- **_FakeProc** (15 connections) — `runtime/tests/test_tunnel.py`
- **_FakeStartEngine** (14 connections) — `core/tests/test_cloud_reconcile.py`
- **_seed_finished_run()** (13 connections) — `deploy_aws/tests/test_lambda_handlers.py`
- **BoomLauncher** (12 connections) — `core/tests/test_reconcile.py`
- **_OrderRecordingRunStore** (12 connections) — `core/tests/test_reconcile.py`
- **ConflictException** (12 connections) — `deploy_aws/tests/test_lambda_handlers.py`
- **exceptions** (12 connections) — `deploy_aws/tests/test_lambda_handlers.py`
- **test_report_still_written_when_the_run_duration_read_fails()** (12 connections) — `deploy_aws/tests/test_lambda_handlers.py`
- **test_explain_to_dict_drops_unmatched_scopes_and_keeps_job_fact()** (11 connections) — `cli/tests/test_main.py`
- **test_build_wires_arg_offloader_so_step_argument_bodies_read_back()** (11 connections) — `deploy_aws/tests/test_lambda_handlers.py`
- **test_detached_flag_on_state_item()** (10 connections) — `core/tests/test_ddb_run_store.py`
- **test_worker_task_def_arns_on_state_item()** (10 connections) — `core/tests/test_ddb_run_store.py`
- **_explain_job()** (9 connections) — `cli/tests/test_main.py`
- *... and 55 more nodes in this community*

## Relationships

- [Run Result Aggregation Tree](Run_Result_Aggregation_Tree.md) (64 shared connections)
- [Cloud Store Adapters](Cloud_Store_Adapters.md) (54 shared connections)
- [Run State Store](Run_State_Store.md) (47 shared connections)
- [Reconciler Orchestration](Reconciler_Orchestration.md) (30 shared connections)
- [Typed Errors and Wire Protocol](Typed_Errors_and_Wire_Protocol.md) (25 shared connections)
- [Event Log Adapters](Event_Log_Adapters.md) (21 shared connections)
- [Cloud Integration Tests](Cloud_Integration_Tests.md) (16 shared connections)
- [Lambda Handler Tests](Lambda_Handler_Tests.md) (16 shared connections)
- [Run Scheduling Core](Run_Scheduling_Core.md) (15 shared connections)
- [Cloud Launcher](Cloud_Launcher.md) (13 shared connections)
- [Subprocess Engine Adapter Tests](Subprocess_Engine_Adapter_Tests.md) (13 shared connections)
- [ECS Timeout Handling Tests](ECS_Timeout_Handling_Tests.md) (12 shared connections)

## Source Files

- `cli/tests/test_main.py`
- `core/DEVELOPMENT.md`
- `core/gherkai_core/adapters/cloud_launcher.py`
- `core/gherkai_core/adapters/fargate_engine.py`
- `core/gherkai_core/adapters/subprocess_engine.py`
- `core/gherkai_core/model.py`
- `core/tests/test_arg_offload.py`
- `core/tests/test_cloud_reconcile.py`
- `core/tests/test_ddb_run_store.py`
- `core/tests/test_project.py`
- `core/tests/test_reconcile.py`
- `core/tests/test_subprocess_engine.py`
- `core/tests/test_wire.py`
- `deploy_aws/tests/test_lambda_handlers.py`
- `runtime/tests/test_tunnel.py`
- `runtime/tests/test_tunnel_host.py`

## Audit Trail

- EXTRACTED: 578 (77%)
- INFERRED: 168 (23%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*