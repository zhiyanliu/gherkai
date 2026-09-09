# AWS Deploy Provider

> 66 nodes · cohesion 0.07

## Key Concepts

- **Provider** (80 connections) — `deploy_aws/gherkai_deploy_aws/cli.py`
- **test_provider.py** (79 connections) — `deploy_aws/tests/test_provider.py`
- **_parse()** (46 connections) — `deploy_aws/tests/test_provider.py`
- **_stub_backend()** (16 connections) — `deploy_aws/tests/test_provider.py`
- **_argv()** (9 connections) — `deploy_aws/tests/test_provider.py`
- **test_synth_only_pins_a_relative_dir_to_the_callers_cwd()** (6 connections) — `deploy_aws/tests/test_provider.py`
- **test_bootstrap_needs_no_vpc_and_never_loads_the_app()** (5 connections) — `deploy_aws/tests/test_provider.py`
- **test_deploy_passes_require_approval_through()** (5 connections) — `deploy_aws/tests/test_provider.py`
- **test_deploy_runs_the_worker_image_steps_after_a_successful_cdk()** (5 connections) — `deploy_aws/tests/test_provider.py`
- **test_deploy_skips_the_worker_image_steps_when_cdk_fails()** (5 connections) — `deploy_aws/tests/test_provider.py`
- **test_deploy_without_require_approval_leaves_it_to_cdk()** (5 connections) — `deploy_aws/tests/test_provider.py`
- **test_destroy_yes_passes_force_to_cdk_and_is_off_by_default()** (5 connections) — `deploy_aws/tests/test_provider.py`
- **test_diff_invokes_cdk_with_app_output_and_context()** (5 connections) — `deploy_aws/tests/test_provider.py`
- **test_missing_node_reports_cleanly_and_skips_cdk()** (5 connections) — `deploy_aws/tests/test_provider.py`
- **_parse_destroy()** (4 connections) — `deploy_aws/tests/test_provider.py`
- **test_delete_worker_is_a_documented_placeholder()** (4 connections) — `deploy_aws/tests/test_provider.py`
- **test_deploy_blocked_by_vpc_guard_never_invokes_cdk()** (4 connections) — `deploy_aws/tests/test_provider.py`
- **test_destroy_invokes_cdk_destroy_with_same_context()** (4 connections) — `deploy_aws/tests/test_provider.py`
- **test_guard_first_deploy_proceeds()** (4 connections) — `deploy_aws/tests/test_provider.py`
- **test_guard_match_proceeds()** (4 connections) — `deploy_aws/tests/test_provider.py`
- **test_guard_mismatch_allowed()** (4 connections) — `deploy_aws/tests/test_provider.py`
- **test_guard_mismatch_blocks()** (4 connections) — `deploy_aws/tests/test_provider.py`
- **test_guard_unexpected_read_error_exits_2_not_traceback()** (4 connections) — `deploy_aws/tests/test_provider.py`
- **test_guard_unrecorded_allowed_once()** (4 connections) — `deploy_aws/tests/test_provider.py`
- **test_guard_unrecorded_blocks_and_points_at_diff()** (4 connections) — `deploy_aws/tests/test_provider.py`
- *... and 41 more nodes in this community*

## Relationships

- [CDK Context Cache](CDK_Context_Cache.md) (18 shared connections)
- [Provider Deploy Commands](Provider_Deploy_Commands.md) (16 shared connections)
- [CDK Invocation Tests](CDK_Invocation_Tests.md) (14 shared connections)
- [CDK App & Deploy CLI](CDK_App_%26_Deploy_CLI.md) (10 shared connections)
- [VPC State Classification](VPC_State_Classification.md) (9 shared connections)
- [AWS Client Stubs (CFN/SSM)](AWS_Client_Stubs_%28CFN-SSM%29.md) (8 shared connections)
- [Provider Flag Wiring](Provider_Flag_Wiring.md) (6 shared connections)
- [Unimplemented Delete Worker](Unimplemented_Delete_Worker.md) (1 shared connections)
- [Container Engine Adapter](Container_Engine_Adapter.md) (1 shared connections)
- [Provider Import Isolation](Provider_Import_Isolation.md) (1 shared connections)

## Source Files

- `deploy_aws/gherkai_deploy_aws/cli.py`
- `deploy_aws/tests/test_provider.py`

## Audit Trail

- EXTRACTED: 237 (97%)
- INFERRED: 7 (3%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*