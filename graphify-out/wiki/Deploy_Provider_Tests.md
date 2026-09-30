# Deploy Provider Tests

> 64 nodes · cohesion 0.06

## Key Concepts

- **test_provider.py** (90 connections) — `deploy_aws/tests/test_provider.py`
- **_parse()** (52 connections) — `deploy_aws/tests/test_provider.py`
- **_stub_backend()** (21 connections) — `deploy_aws/tests/test_provider.py`
- **_argv()** (9 connections) — `deploy_aws/tests/test_provider.py`
- **test_deploy_warns_about_missing_container_engine_only_for_pure_release_versions()** (6 connections) — `deploy_aws/tests/test_provider.py`
- **test_bootstrap_needs_no_vpc_and_never_loads_the_app()** (5 connections) — `deploy_aws/tests/test_provider.py`
- **test_deploy_passes_require_approval_through()** (5 connections) — `deploy_aws/tests/test_provider.py`
- **test_deploy_runs_the_worker_image_steps_after_a_successful_cdk()** (5 connections) — `deploy_aws/tests/test_provider.py`
- **test_deploy_skips_the_worker_image_steps_when_cdk_fails()** (5 connections) — `deploy_aws/tests/test_provider.py`
- **test_deploy_without_require_approval_leaves_it_to_cdk()** (5 connections) — `deploy_aws/tests/test_provider.py`
- **test_missing_node_reports_cleanly_and_skips_cdk()** (5 connections) — `deploy_aws/tests/test_provider.py`
- **test_vpc_absent_hint_for_existing_environment_without_record()** (5 connections) — `deploy_aws/tests/test_provider.py`
- **test_vpc_absent_hint_names_the_recorded_tier_for_an_existing_environment()** (5 connections) — `deploy_aws/tests/test_provider.py`
- **test_vpc_absent_parses_but_every_synthesizing_verb_exits_2()** (5 connections) — `deploy_aws/tests/test_provider.py`
- **test_a_bad_profile_exits_2_at_the_entry_not_a_traceback()** (4 connections) — `deploy_aws/tests/test_provider.py`
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
- *... and 39 more nodes in this community*

## Relationships

- [AWS Deploy Provider](AWS_Deploy_Provider.md) (43 shared connections)
- [CDK Context Cache](CDK_Context_Cache.md) (17 shared connections)
- [Deploy CLI Backend Helpers](Deploy_CLI_Backend_Helpers.md) (11 shared connections)
- [CDK Deploy Argv Tests](CDK_Deploy_Argv_Tests.md) (11 shared connections)
- [AWS Client Stubs](AWS_Client_Stubs.md) (5 shared connections)
- [CDK Destroy Confirmation](CDK_Destroy_Confirmation.md) (4 shared connections)
- [Container Engine Probe Stub](Container_Engine_Probe_Stub.md) (2 shared connections)
- [CDK App & Backend Stack](CDK_App_%26_Backend_Stack.md) (1 shared connections)
- [SSM Path Naming](SSM_Path_Naming.md) (1 shared connections)
- [Container Engine Errors](Container_Engine_Errors.md) (1 shared connections)
- [CLI Test Fixtures](CLI_Test_Fixtures.md) (1 shared connections)
- [Provider Module Import Guard](Provider_Module_Import_Guard.md) (1 shared connections)

## Source Files

- `deploy_aws/tests/test_provider.py`

## Audit Trail

- EXTRACTED: 223 (100%)
- INFERRED: 0 (0%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*