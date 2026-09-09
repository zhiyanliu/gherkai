# Provider

> God node · 80 connections · `deploy_aws/gherkai_deploy_aws/cli.py`

**Community:** [AWS Deploy Provider CLI](AWS_Deploy_Provider_CLI.md)

## Connections by Relation

### calls
- _parse() `EXTRACTED`
- test_context_cache_is_saved_after_the_run_and_seeded_into_the_next_fresh_work_dir() `EXTRACTED`
- test_context_cache_survives_a_failed_cdk_run() `EXTRACTED`
- test_synth_only_pins_a_relative_dir_to_the_callers_cwd() `EXTRACTED`
- test_bootstrap_needs_no_vpc_and_never_loads_the_app() `EXTRACTED`
- test_deploy_passes_require_approval_through() `EXTRACTED`
- test_deploy_rejects_an_unimplemented_container_engine_before_touching_the_account() `EXTRACTED`
- test_deploy_runs_the_worker_image_steps_after_a_successful_cdk() `EXTRACTED`
- test_deploy_skips_the_worker_image_steps_when_cdk_fails() `EXTRACTED`
- test_deploy_without_require_approval_leaves_it_to_cdk() `EXTRACTED`
- test_destroy_yes_passes_force_to_cdk_and_is_off_by_default() `EXTRACTED`
- test_diff_invokes_cdk_with_app_output_and_context() `EXTRACTED`
- test_missing_node_reports_cleanly_and_skips_cdk() `EXTRACTED`
- test_refresh_context_discards_the_cache_before_running() `EXTRACTED`
- _parse_destroy() `EXTRACTED`
- test_cdk_returncode_is_passed_through() `EXTRACTED`
- test_cdk_runs_in_the_work_dir_which_holds_the_generated_cdk_json() `EXTRACTED`
- test_delete_worker_is_a_documented_placeholder() `EXTRACTED`
- test_deploy_blocked_by_vpc_guard_never_invokes_cdk() `EXTRACTED`
- test_destroy_invokes_cdk_destroy_with_same_context() `EXTRACTED`

### contains
- cli.py `EXTRACTED`

### imports
- test_provider.py `EXTRACTED`

### method
- ._run_cdk() `EXTRACTED`
- ._guard_vpc_spec() `EXTRACTED`
- ._resolve_target() `EXTRACTED`
- .add_arguments() `EXTRACTED`
- .deploy() `EXTRACTED`
- .bootstrap() `EXTRACTED`
- ._add_worker_subverbs() `EXTRACTED`
- .synth_only() `EXTRACTED`
- ._container_engine() `EXTRACTED`
- ._worker_image_steps() `EXTRACTED`
- ._require_vpc() `EXTRACTED`
- .build_context() `EXTRACTED`
- ._resolve_version() `EXTRACTED`
- ._add_container_engine_flag() `EXTRACTED`
- .push_worker() `EXTRACTED`
- .write_cdk_json() `EXTRACTED`
- ._work_dir() `EXTRACTED`
- ._is_destroy_parser() `EXTRACTED`
- ._declares_worker_subverbs() `EXTRACTED`
- ._add_locator_flags() `EXTRACTED`

### rationale_for
- AWS provider——`gherkai deploy` 族命令在 AWS 上的实现（接缝契约见模块头）。 `EXTRACTED`

### uses
- _Recorder `INFERRED`
- _CdkWritingContext `INFERRED`
- UnsupportedContainerEngine `INFERRED`
- _ClientError `INFERRED`
- _Cfn `INFERRED`
- _FakeEngine `INFERRED`
- _Ssm `INFERRED`

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*