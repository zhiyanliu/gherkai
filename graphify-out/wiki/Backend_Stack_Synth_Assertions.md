# Backend Stack Synth Assertions

> 47 nodes · cohesion 0.07

## Key Concepts

- **test_stack.py** (52 connections) — `deploy_aws/tests/test_stack.py`
- **make_template()** (47 connections) — `deploy_aws/tests/synth_fixture.py`
- **test_advancers_can_read_backend_ssm_params_for_the_compat_fallback()** (3 connections) — `deploy_aws/tests/test_stack.py`
- **test_ecr_repos_have_no_lifecycle_rules_and_are_retained()** (3 connections) — `deploy_aws/tests/test_stack.py`
- **test_events_table_has_no_gsi()** (3 connections) — `deploy_aws/tests/test_stack.py`
- **test_exit_observer_can_read_runs_table_only()** (3 connections) — `deploy_aws/tests/test_stack.py`
- **test_reconcile_lambdas_share_per_run_concurrency_cap()** (3 connections) — `deploy_aws/tests/test_stack.py`
- **test_runs_table_has_the_sparse_status_gsi_for_worker_cleanup()** (3 connections) — `deploy_aws/tests/test_stack.py`
- **test_task_role_resource_arns_narrowed()** (3 connections) — `deploy_aws/tests/test_stack.py`
- **test_worker_template_arn_is_not_injected_into_any_lambda_env()** (3 connections) — `deploy_aws/tests/test_stack.py`
- **test_artifacts_bucket_job_in_lifecycle()** (2 connections) — `deploy_aws/tests/test_stack.py`
- **test_artifacts_bucket_private()** (2 connections) — `deploy_aws/tests/test_stack.py`
- **test_ecs_stopped_eventbridge_rule()** (2 connections) — `deploy_aws/tests/test_stack.py`
- **test_events_table_has_stream()** (2 connections) — `deploy_aws/tests/test_stack.py`
- **test_events_table_seq_is_number_type()** (2 connections) — `deploy_aws/tests/test_stack.py`
- **test_execution_role_and_two_task_roles()** (2 connections) — `deploy_aws/tests/test_stack.py`
- **test_kicker_mapping_insert_filter()** (2 connections) — `deploy_aws/tests/test_stack.py`
- **test_reconcile_lambdas_present()** (2 connections) — `deploy_aws/tests/test_stack.py`
- **test_reconciler_can_runtask_and_passrole()** (2 connections) — `deploy_aws/tests/test_stack.py`
- **test_runs_table_has_stream_for_kicker()** (2 connections) — `deploy_aws/tests/test_stack.py`
- **test_ssm_params_with_prefix_path()** (2 connections) — `deploy_aws/tests/test_stack.py`
- **test_stop_timeout_accepts_lower_boundary_1()** (2 connections) — `deploy_aws/tests/test_stack.py`
- **test_stop_timeout_accepts_upper_boundary_120()** (2 connections) — `deploy_aws/tests/test_stack.py`
- **test_stop_timeout_context_override()** (2 connections) — `deploy_aws/tests/test_stack.py`
- **test_stop_timeout_defaults_to_120s()** (2 connections) — `deploy_aws/tests/test_stack.py`
- *... and 22 more nodes in this community*

## Relationships

- [CDK SSM Parameter Guardrails](CDK_SSM_Parameter_Guardrails.md) (15 shared connections)
- [Stack Synth Fixtures](Stack_Synth_Fixtures.md) (4 shared connections)
- [Worker Subnet Single Source](Worker_Subnet_Single_Source.md) (3 shared connections)
- [Backend Stack Constructs](Backend_Stack_Constructs.md) (2 shared connections)
- [CDK App & Deploy CLI](CDK_App_%26_Deploy_CLI.md) (1 shared connections)

## Source Files

- `deploy_aws/tests/synth_fixture.py`
- `deploy_aws/tests/test_stack.py`

## Audit Trail

- EXTRACTED: 106 (100%)
- INFERRED: 0 (0%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*