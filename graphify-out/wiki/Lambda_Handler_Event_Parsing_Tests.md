# Lambda Handler Event Parsing Tests

> 122 nodes · cohesion 0.03

## Key Concepts

- **test_lambda_handlers.py** (74 connections) — `deploy_aws/tests/test_lambda_handlers.py`
- **_FakeEcs** (25 connections) — `deploy_aws/tests/test_lambda_handlers.py`
- **_seed_run()** (23 connections) — `deploy_aws/tests/test_lambda_handlers.py`
- **_timeout_built()** (20 connections) — `deploy_aws/tests/test_lambda_handlers.py`
- **_stream_record()** (14 connections) — `deploy_aws/tests/test_lambda_handlers.py`
- **_seed_finished_run()** (13 connections) — `deploy_aws/tests/test_lambda_handlers.py`
- **_stopped_detail()** (10 connections) — `deploy_aws/tests/test_lambda_handlers.py`
- **_seed_worker_ssm()** (5 connections) — `deploy_aws/tests/test_lambda_handlers.py`
- **test_finished_run_gate_keys_on_the_committed_run_status_only()** (5 connections) — `deploy_aws/tests/test_lambda_handlers.py`
- **test_finished_run_is_not_reprojected_by_a_late_or_replayed_event()** (5 connections) — `deploy_aws/tests/test_lambda_handlers.py`
- **test_handle_timeout_finds_stopped_target_on_second_page()** (5 connections) — `deploy_aws/tests/test_lambda_handlers.py`
- **test_handle_timeout_pages_task_lists_and_batches_describe()** (5 connections) — `deploy_aws/tests/test_lambda_handlers.py`
- **_report_bytes()** (4 connections) — `deploy_aws/tests/test_lambda_handlers.py`
- **_stopped_filler()** (4 connections) — `deploy_aws/tests/test_lambda_handlers.py`
- **test_build_falls_back_to_default_pointer_for_legacy_definition()** (4 connections) — `deploy_aws/tests/test_lambda_handlers.py`
- **test_build_uses_definition_worker_task_defs_verbatim()** (4 connections) — `deploy_aws/tests/test_lambda_handlers.py`
- **test_exit_observer_records_exit_for_detached_run()** (4 connections) — `deploy_aws/tests/test_lambda_handlers.py`
- **test_exit_observer_skips_non_detached_run()** (4 connections) — `deploy_aws/tests/test_lambda_handlers.py`
- **test_handle_timeout_converges_directly_when_task_gone()** (4 connections) — `deploy_aws/tests/test_lambda_handlers.py`
- **test_handle_timeout_converges_from_describe_keeps_timeout_attribution_of_own_stop()** (4 connections) — `deploy_aws/tests/test_lambda_handlers.py`
- **test_handle_timeout_converges_from_describe_when_task_already_stopped()** (4 connections) — `deploy_aws/tests/test_lambda_handlers.py`
- **test_handle_timeout_leaves_a_stopping_task_to_the_observer()** (4 connections) — `deploy_aws/tests/test_lambda_handlers.py`
- **test_handle_timeout_noop_when_exit_in_flight()** (4 connections) — `deploy_aws/tests/test_lambda_handlers.py`
- **test_handle_timeout_noop_when_job_terminal()** (4 connections) — `deploy_aws/tests/test_lambda_handlers.py`
- **test_handle_timeout_stops_matching_task()** (4 connections) — `deploy_aws/tests/test_lambda_handlers.py`
- *... and 97 more nodes in this community*

## Relationships

- [Job Explain Data Model](Job_Explain_Data_Model.md) (22 shared connections)
- [Run State Store](Run_State_Store.md) (6 shared connections)
- [DynamoDB Job State Store](DynamoDB_Job_State_Store.md) (5 shared connections)
- [Step Argument S3 Offload](Step_Argument_S3_Offload.md) (5 shared connections)
- [Reconcile Lambdas](Reconcile_Lambdas.md) (2 shared connections)
- [Cloud Adapter Boundary Modules](Cloud_Adapter_Boundary_Modules.md) (2 shared connections)
- [Result Tree Rendering](Result_Tree_Rendering.md) (1 shared connections)
- [Detached Local Run Host](Detached_Local_Run_Host.md) (1 shared connections)
- [Test Fixtures And Env](Test_Fixtures_And_Env.md) (1 shared connections)
- [Cloud Launcher Reconcile Tests](Cloud_Launcher_Reconcile_Tests.md) (1 shared connections)
- [SQLite Event Log](SQLite_Event_Log.md) (1 shared connections)

## Source Files

- `core/gherkai_core/model.py`
- `deploy_aws/tests/test_lambda_handlers.py`

## Audit Trail

- EXTRACTED: 221 (94%)
- INFERRED: 13 (6%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*