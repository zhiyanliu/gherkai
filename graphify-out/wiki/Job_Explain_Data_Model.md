# Job Explain Data Model

> 92 nodes · cohesion 0.05

## Key Concepts

- **Job** (135 connections) — `core/gherkai_core/model.py`
- **RunMeta** (120 connections) — `core/gherkai_core/model.py`
- **Scenario** (73 connections) — `core/gherkai_core/model.py`
- **Step** (72 connections) — `core/gherkai_core/model.py`
- **DynamoDBRunStore** (40 connections) — `core/gherkai_core/adapters/run_store/ddb.py`
- **test_cloud_integration.py** (32 connections) — `core/tests/test_cloud_integration.py`
- **StepArgument** (31 connections) — `core/gherkai_core/model.py`
- **test_arg_offload.py** (23 connections) — `core/tests/test_arg_offload.py`
- **_FakeProc** (15 connections) — `runtime/tests/test_tunnel.py`
- **test_offload_unblocks_oversized_docstring_real()** (12 connections) — `core/tests/test_cloud_integration.py`
- **_OrderRecordingRunStore** (12 connections) — `core/tests/test_reconcile.py`
- **ConflictException** (12 connections) — `deploy_aws/tests/test_lambda_handlers.py`
- **exceptions** (12 connections) — `deploy_aws/tests/test_lambda_handlers.py`
- **test_report_still_written_when_the_run_duration_read_fails()** (12 connections) — `deploy_aws/tests/test_lambda_handlers.py`
- **test_explain_to_dict_drops_unmatched_scopes_and_keeps_job_fact()** (11 connections) — `cli/tests/test_main.py`
- **test_offload_round_trip_real()** (11 connections) — `core/tests/test_cloud_integration.py`
- **test_build_wires_arg_offloader_so_step_argument_bodies_read_back()** (11 connections) — `deploy_aws/tests/test_lambda_handlers.py`
- **_uniq()** (10 connections) — `core/tests/test_cloud_integration.py`
- **test_detached_flag_on_state_item()** (10 connections) — `core/tests/test_ddb_run_store.py`
- **test_worker_task_def_arns_on_state_item()** (10 connections) — `core/tests/test_ddb_run_store.py`
- **_explain_job()** (9 connections) — `cli/tests/test_main.py`
- **test_meta_json_holds_pointers_not_payload()** (9 connections) — `core/tests/test_arg_offload.py`
- **test_reader_without_offloader_fails_loud_on_offloaded_meta()** (9 connections) — `core/tests/test_arg_offload.py`
- **test_reader_without_offloader_not_fooled_by_content_ref_as_text()** (9 connections) — `core/tests/test_arg_offload.py`
- **test_restore_uses_uri_not_current_prefix()** (9 connections) — `core/tests/test_arg_offload.py`
- *... and 67 more nodes in this community*

## Relationships

- [DynamoDB Job State Store](DynamoDB_Job_State_Store.md) (49 shared connections)
- [Cloud Adapter Boundary Modules](Cloud_Adapter_Boundary_Modules.md) (48 shared connections)
- [Run State Store](Run_State_Store.md) (39 shared connections)
- [EventLog And Launcher Ports](EventLog_And_Launcher_Ports.md) (27 shared connections)
- [Lambda Handler Event Parsing Tests](Lambda_Handler_Event_Parsing_Tests.md) (22 shared connections)
- [Step Argument S3 Offload](Step_Argument_S3_Offload.md) (20 shared connections)
- [Run Scheduling Events Core](Run_Scheduling_Events_Core.md) (19 shared connections)
- [Cloud Launcher Reconcile Tests](Cloud_Launcher_Reconcile_Tests.md) (18 shared connections)
- [Result Tree Rendering](Result_Tree_Rendering.md) (16 shared connections)
- [Reconciler Event Projection](Reconciler_Event_Projection.md) (14 shared connections)
- [Feature File Parsing](Feature_File_Parsing.md) (13 shared connections)
- [Conditional Write Guards](Conditional_Write_Guards.md) (12 shared connections)

## Source Files

- `cli/tests/test_main.py`
- `core/gherkai_core/adapters/run_store/ddb.py`
- `core/gherkai_core/model.py`
- `core/tests/test_arg_offload.py`
- `core/tests/test_cloud_integration.py`
- `core/tests/test_ddb_run_store.py`
- `core/tests/test_project.py`
- `core/tests/test_reconcile.py`
- `core/tests/test_sqlite_event_log.py`
- `core/tests/test_subprocess_engine.py`
- `core/tests/test_wire.py`
- `deploy_aws/tests/test_lambda_handlers.py`
- `runtime/tests/test_tunnel.py`
- `runtime/tests/test_tunnel_host.py`

## Audit Trail

- EXTRACTED: 516 (76%)
- INFERRED: 160 (24%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*