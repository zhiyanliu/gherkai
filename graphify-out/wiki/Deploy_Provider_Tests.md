# Deploy Provider Tests

> 49 nodes · cohesion 0.08

## Key Concepts

- **test_provider.py** (85 connections) — `deploy_aws/tests/test_provider.py`
- **_parse()** (48 connections) — `deploy_aws/tests/test_provider.py`
- **_stub_backend()** (17 connections) — `deploy_aws/tests/test_provider.py`
- **test_deploy_passes_require_approval_through()** (5 connections) — `deploy_aws/tests/test_provider.py`
- **test_deploy_runs_the_worker_image_steps_after_a_successful_cdk()** (5 connections) — `deploy_aws/tests/test_provider.py`
- **test_deploy_skips_the_worker_image_steps_when_cdk_fails()** (5 connections) — `deploy_aws/tests/test_provider.py`
- **test_deploy_without_require_approval_leaves_it_to_cdk()** (5 connections) — `deploy_aws/tests/test_provider.py`
- **test_missing_node_reports_cleanly_and_skips_cdk()** (5 connections) — `deploy_aws/tests/test_provider.py`
- **test_delete_worker_is_a_documented_placeholder()** (4 connections) — `deploy_aws/tests/test_provider.py`
- **test_deploy_blocked_by_vpc_guard_never_invokes_cdk()** (4 connections) — `deploy_aws/tests/test_provider.py`
- **test_guard_first_deploy_proceeds()** (4 connections) — `deploy_aws/tests/test_provider.py`
- **test_guard_match_proceeds()** (4 connections) — `deploy_aws/tests/test_provider.py`
- **test_guard_mismatch_allowed()** (4 connections) — `deploy_aws/tests/test_provider.py`
- **test_guard_mismatch_blocks()** (4 connections) — `deploy_aws/tests/test_provider.py`
- **test_guard_unexpected_read_error_exits_2_not_traceback()** (4 connections) — `deploy_aws/tests/test_provider.py`
- **test_guard_unrecorded_allowed_once()** (4 connections) — `deploy_aws/tests/test_provider.py`
- **test_guard_unrecorded_blocks_and_points_at_diff()** (4 connections) — `deploy_aws/tests/test_provider.py`
- **test_tolerates_a_shell_that_declares_neither_command_face_flag()** (4 connections) — `deploy_aws/tests/test_provider.py`
- **test_version_falls_back_to_installed_dist_version()** (4 connections) — `deploy_aws/tests/test_provider.py`
- **test_vpc_absent_parses_but_every_synthesizing_verb_exits_2()** (4 connections) — `deploy_aws/tests/test_provider.py`
- **parametrize** (3 connections)
- **test_asset_dir_env_points_into_the_work_dir()** (3 connections) — `deploy_aws/tests/test_provider.py`
- **test_bare_deploy_still_parses_with_subverbs_present()** (3 connections) — `deploy_aws/tests/test_provider.py`
- **test_bootstrap_without_resolvable_region_exits_2()** (3 connections) — `deploy_aws/tests/test_provider.py`
- **test_context_default_dossier_sets_use_default_vpc()** (3 connections) — `deploy_aws/tests/test_provider.py`
- *... and 24 more nodes in this community*

## Relationships

- [AWS Deploy Provider](AWS_Deploy_Provider.md) (36 shared connections)
- [CDK Bootstrap/Destroy CLI](CDK_Bootstrap-Destroy_CLI.md) (16 shared connections)
- [Deploy CLI Test Doubles](Deploy_CLI_Test_Doubles.md) (10 shared connections)
- [CDK Context Cache](CDK_Context_Cache.md) (9 shared connections)
- [VPC State & Deploy Flow](VPC_State_%26_Deploy_Flow.md) (5 shared connections)
- [CloudFormation/SSM Test Doubles](CloudFormation-SSM_Test_Doubles.md) (5 shared connections)
- [CDK App & AWS Provider CLI](CDK_App_%26_AWS_Provider_CLI.md) (4 shared connections)
- [Container Engine Absence Warning](Container_Engine_Absence_Warning.md) (4 shared connections)
- [CDK Toolchain Preflight](CDK_Toolchain_Preflight.md) (3 shared connections)
- [Container Engine Adapter](Container_Engine_Adapter.md) (1 shared connections)
- [AWS Test Fixtures](AWS_Test_Fixtures.md) (1 shared connections)
- [Provider Import Isolation](Provider_Import_Isolation.md) (1 shared connections)

## Source Files

- `deploy_aws/tests/test_provider.py`

## Audit Trail

- EXTRACTED: 190 (100%)
- INFERRED: 0 (0%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*