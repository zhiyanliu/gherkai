# AWS Deploy Provider Tests

> 88 nodes · cohesion 0.05

## Key Concepts

- **Provider** (100 connections) — `deploy_aws/gherkai_deploy_aws/cli.py`
- **test_provider.py** (90 connections) — `deploy_aws/tests/test_provider.py`
- **_parse()** (52 connections) — `deploy_aws/tests/test_provider.py`
- **_stub_backend()** (21 connections) — `deploy_aws/tests/test_provider.py`
- **_argv()** (9 connections) — `deploy_aws/tests/test_provider.py`
- **test_deploy_warns_about_missing_container_engine_only_for_pure_release_versions()** (6 connections) — `deploy_aws/tests/test_provider.py`
- **test_synth_only_pins_a_relative_dir_to_the_callers_cwd()** (6 connections) — `deploy_aws/tests/test_provider.py`
- **_AbsentEngine** (5 connections) — `deploy_aws/tests/test_provider.py`
- **test_bootstrap_needs_no_vpc_and_never_loads_the_app()** (5 connections) — `deploy_aws/tests/test_provider.py`
- **test_deploy_passes_require_approval_through()** (5 connections) — `deploy_aws/tests/test_provider.py`
- **test_deploy_rejects_an_unimplemented_container_engine_before_touching_the_account()** (5 connections) — `deploy_aws/tests/test_provider.py`
- **test_deploy_runs_the_worker_image_steps_after_a_successful_cdk()** (5 connections) — `deploy_aws/tests/test_provider.py`
- **test_deploy_skips_the_worker_image_steps_when_cdk_fails()** (5 connections) — `deploy_aws/tests/test_provider.py`
- **test_deploy_without_require_approval_leaves_it_to_cdk()** (5 connections) — `deploy_aws/tests/test_provider.py`
- **test_destroy_yes_passes_force_to_cdk_and_is_off_by_default()** (5 connections) — `deploy_aws/tests/test_provider.py`
- **test_diff_invokes_cdk_with_app_output_and_context()** (5 connections) — `deploy_aws/tests/test_provider.py`
- **test_missing_node_reports_cleanly_and_skips_cdk()** (5 connections) — `deploy_aws/tests/test_provider.py`
- **test_vpc_absent_hint_for_existing_environment_without_record()** (5 connections) — `deploy_aws/tests/test_provider.py`
- **test_vpc_absent_hint_names_the_recorded_tier_for_an_existing_environment()** (5 connections) — `deploy_aws/tests/test_provider.py`
- **test_vpc_absent_parses_but_every_synthesizing_verb_exits_2()** (5 connections) — `deploy_aws/tests/test_provider.py`
- **_parse_destroy()** (4 connections) — `deploy_aws/tests/test_provider.py`
- **test_a_bad_profile_exits_2_at_the_entry_not_a_traceback()** (4 connections) — `deploy_aws/tests/test_provider.py`
- **test_cdk_returncode_is_passed_through()** (4 connections) — `deploy_aws/tests/test_provider.py`
- **test_cdk_runs_in_the_work_dir_which_holds_the_generated_cdk_json()** (4 connections) — `deploy_aws/tests/test_provider.py`
- **test_delete_worker_is_a_documented_placeholder()** (4 connections) — `deploy_aws/tests/test_provider.py`
- *... and 63 more nodes in this community*

## Relationships

- [CDK Command Wrapper](CDK_Command_Wrapper.md) (21 shared connections)
- [AWS Deploy CLI Provider](AWS_Deploy_CLI_Provider.md) (19 shared connections)
- [CDK Context Cache](CDK_Context_Cache.md) (16 shared connections)
- [Deploy Prerequisite Stubs](Deploy_Prerequisite_Stubs.md) (12 shared connections)
- [CloudFormation/SSM Fakes](CloudFormation-SSM_Fakes.md) (8 shared connections)
- [Deploy CLI Flag Parsers](Deploy_CLI_Flag_Parsers.md) (6 shared connections)
- [Container Engine Port](Container_Engine_Port.md) (3 shared connections)
- [Skill Deploy Token Guards](Skill_Deploy_Token_Guards.md) (2 shared connections)
- [CDK App & Backend Stack](CDK_App_%26_Backend_Stack.md) (2 shared connections)
- [Worker Delete Command Stub](Worker_Delete_Command_Stub.md) (1 shared connections)
- [AWS Worker Image Registry](AWS_Worker_Image_Registry.md) (1 shared connections)
- [Contributor Docs And ADRs](Contributor_Docs_And_ADRs.md) (1 shared connections)

## Source Files

- `deploy_aws/gherkai_deploy_aws/cli.py`
- `deploy_aws/tests/test_provider.py`

## Audit Trail

- EXTRACTED: 292 (97%)
- INFERRED: 8 (3%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*