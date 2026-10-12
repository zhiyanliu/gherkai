# Deploy Provider & Container Seam

> 74 nodes · cohesion 0.06

## Key Concepts

- **Provider** (100 connections) — `deploy_aws/gherkai_deploy_aws/cli.py`
- **test_provider.py** (90 connections) — `deploy_aws/tests/test_provider.py`
- **_parse()** (52 connections) — `deploy_aws/tests/test_provider.py`
- **_stub_backend()** (21 connections) — `deploy_aws/tests/test_provider.py`
- **container.py** (14 connections) — `deploy_aws/gherkai_deploy_aws/container.py`
- **test_deploy_warns_about_missing_container_engine_only_for_pure_release_versions()** (6 connections) — `deploy_aws/tests/test_provider.py`
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
- **test_guard_first_deploy_proceeds()** (4 connections) — `deploy_aws/tests/test_provider.py`
- **test_guard_match_proceeds()** (4 connections) — `deploy_aws/tests/test_provider.py`
- **test_guard_mismatch_allowed()** (4 connections) — `deploy_aws/tests/test_provider.py`
- **test_guard_mismatch_blocks()** (4 connections) — `deploy_aws/tests/test_provider.py`
- **test_guard_unexpected_read_error_exits_2_not_traceback()** (4 connections) — `deploy_aws/tests/test_provider.py`
- **test_guard_unrecorded_allowed_once()** (4 connections) — `deploy_aws/tests/test_provider.py`
- **test_guard_unrecorded_blocks_and_points_at_diff()** (4 connections) — `deploy_aws/tests/test_provider.py`
- **test_tolerates_a_shell_that_declares_neither_command_face_flag()** (4 connections) — `deploy_aws/tests/test_provider.py`
- *... and 49 more nodes in this community*

## Relationships

- [CDK Command Invocation](CDK_Command_Invocation.md) (23 shared connections)
- [Deploy Preflight Stubs](Deploy_Preflight_Stubs.md) (15 shared connections)
- [CDK Command Execution](CDK_Command_Execution.md) (14 shared connections)
- [CDK Context Cache](CDK_Context_Cache.md) (13 shared connections)
- [Deploy Provider Commands](Deploy_Provider_Commands.md) (11 shared connections)
- [Container Engine Port](Container_Engine_Port.md) (9 shared connections)
- [VPC State Classification](VPC_State_Classification.md) (9 shared connections)
- [CDK App & AWS Provider CLI](CDK_App_%26_AWS_Provider_CLI.md) (8 shared connections)
- [AWS Client Test Doubles](AWS_Client_Test_Doubles.md) (8 shared connections)
- [Provider CLI Flags](Provider_CLI_Flags.md) (6 shared connections)
- [Absent Container Engine Stub](Absent_Container_Engine_Stub.md) (3 shared connections)
- [Skill Deploy Token Check](Skill_Deploy_Token_Check.md) (2 shared connections)

## Source Files

- `deploy_aws/gherkai_deploy_aws/cli.py`
- `deploy_aws/gherkai_deploy_aws/container.py`
- `deploy_aws/tests/test_provider.py`

## Audit Trail

- EXTRACTED: 286 (97%)
- INFERRED: 8 (3%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*