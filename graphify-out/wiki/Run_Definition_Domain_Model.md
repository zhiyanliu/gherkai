# Run Definition Domain Model

> 58 nodes · cohesion 0.09

## Key Concepts

- **Job** (129 connections) — `core/gherkai_core/model.py`
- **RunMeta** (117 connections) — `core/gherkai_core/model.py`
- **Scenario** (72 connections) — `core/gherkai_core/model.py`
- **Step** (71 connections) — `core/gherkai_core/model.py`
- **StepArgument** (30 connections) — `core/gherkai_core/model.py`
- **test_arg_offload.py** (23 connections) — `core/tests/test_arg_offload.py`
- **_FakeProc** (15 connections) — `runtime/tests/test_tunnel.py`
- **_seed_finished_run()** (13 connections) — `deploy_aws/tests/test_lambda_handlers.py`
- **BoomLauncher** (12 connections) — `core/tests/test_reconcile.py`
- **_OrderRecordingRunStore** (12 connections) — `core/tests/test_reconcile.py`
- **ConflictException** (12 connections) — `deploy_aws/tests/test_lambda_handlers.py`
- **exceptions** (12 connections) — `deploy_aws/tests/test_lambda_handlers.py`
- **test_report_still_written_when_the_run_duration_read_fails()** (12 connections) — `deploy_aws/tests/test_lambda_handlers.py`
- **test_explain_to_dict_drops_unmatched_scopes_and_keeps_job_fact()** (11 connections) — `cli/tests/test_main.py`
- **test_build_wires_arg_offloader_so_step_argument_bodies_read_back()** (11 connections) — `deploy_aws/tests/test_lambda_handlers.py`
- **_explain_job()** (9 connections) — `cli/tests/test_main.py`
- **test_meta_json_holds_pointers_not_payload()** (9 connections) — `core/tests/test_arg_offload.py`
- **test_reader_without_offloader_fails_loud_on_offloaded_meta()** (9 connections) — `core/tests/test_arg_offload.py`
- **test_reader_without_offloader_not_fooled_by_content_ref_as_text()** (9 connections) — `core/tests/test_arg_offload.py`
- **test_restore_uses_uri_not_current_prefix()** (9 connections) — `core/tests/test_arg_offload.py`
- **_job()** (9 connections) — `runtime/tests/test_tunnel_host.py`
- **test_records_feed_project_to_terminal()** (8 connections) — `core/tests/test_sqlite_event_log.py`
- **test_docstring_starting_with_s3_scheme_survives()** (7 connections) — `core/tests/test_arg_offload.py`
- **test_multiple_docstrings_same_scenario_no_collision()** (7 connections) — `core/tests/test_arg_offload.py`
- **test_offload_round_trip_byte_exact()** (7 connections) — `core/tests/test_arg_offload.py`
- *... and 33 more nodes in this community*

## Relationships

- [Result Tree Text Rendering](Result_Tree_Text_Rendering.md) (49 shared connections)
- [DynamoDB Run Store](DynamoDB_Run_Store.md) (45 shared connections)
- [Run State Rendering](Run_State_Rendering.md) (38 shared connections)
- [Worker Log Event Formatting](Worker_Log_Event_Formatting.md) (28 shared connections)
- [Lambda Handler Event Tests](Lambda_Handler_Event_Tests.md) (26 shared connections)
- [Core Adapters Documentation](Core_Adapters_Documentation.md) (24 shared connections)
- [Reconcile Tick and Report](Reconcile_Tick_and_Report.md) (21 shared connections)
- [Cloud Launcher and EventLog](Cloud_Launcher_and_EventLog.md) (19 shared connections)
- [Event Wire Serialization](Event_Wire_Serialization.md) (13 shared connections)
- [Event Records Projection](Event_Records_Projection.md) (12 shared connections)
- [Result Store Serialization](Result_Store_Serialization.md) (10 shared connections)
- [Conditional Write Tests](Conditional_Write_Tests.md) (9 shared connections)

## Source Files

- `cli/tests/test_main.py`
- `core/gherkai_core/model.py`
- `core/tests/test_arg_offload.py`
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

- EXTRACTED: 400 (72%)
- INFERRED: 157 (28%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*