# Deploy Command Shell Tests

> 56 nodes · cohesion 0.07

## Key Concepts

- **test_deploy_cmd.py** (25 connections) — `cli/tests/test_deploy_cmd.py`
- **_StubProvider** (23 connections) — `cli/tests/test_deploy_cmd.py`
- **_FakeEP** (19 connections) — `cli/tests/test_deploy_cmd.py`
- **_patch_eps()** (19 connections) — `cli/tests/test_deploy_cmd.py`
- **test_cli_version_is_handed_to_provider()** (7 connections) — `cli/tests/test_deploy_cmd.py`
- **test_dispatch_maps_command_face_to_provider_method()** (7 connections) — `cli/tests/test_deploy_cmd.py`
- **gherkai_cli/__init__.py** (6 connections) — `cli/gherkai_cli/__init__.py`
- **._record()** (6 connections) — `cli/tests/test_deploy_cmd.py`
- **test_cli_does_not_import_aws_cdk()** (6 connections) — `cli/tests/test_deploy_cmd.py`
- **test_command_face_flags_reach_provider()** (6 connections) — `cli/tests/test_deploy_cmd.py`
- **test_entry_point_class_gets_instantiated()** (6 connections) — `cli/tests/test_deploy_cmd.py`
- **test_multiple_providers_require_provider_flag()** (6 connections) — `cli/tests/test_deploy_cmd.py`
- **test_multiple_providers_selected_by_name()** (6 connections) — `cli/tests/test_deploy_cmd.py`
- **test_provider_exit_code_is_passed_through()** (6 connections) — `cli/tests/test_deploy_cmd.py`
- **test_provider_flags_contributed_and_reach_provider()** (6 connections) — `cli/tests/test_deploy_cmd.py`
- **test_single_provider_needs_no_provider_flag()** (6 connections) — `cli/tests/test_deploy_cmd.py`
- **test_synth_only_dir_lands_on_args()** (6 connections) — `cli/tests/test_deploy_cmd.py`
- **test_three_actions_are_mutually_exclusive()** (6 connections) — `cli/tests/test_deploy_cmd.py`
- **test_provider_load_failure_is_named_not_traceback()** (5 connections) — `cli/tests/test_deploy_cmd.py`
- **test_provider_subverb_seam_takes_precedence()** (5 connections) — `cli/tests/test_deploy_cmd.py`
- **test_unknown_provider_name_lists_installed()** (5 connections) — `cli/tests/test_deploy_cmd.py`
- **test_help_works_without_provider_and_explains_why()** (4 connections) — `cli/tests/test_deploy_cmd.py`
- **test_zero_providers_points_at_the_extra()** (4 connections) — `cli/tests/test_deploy_cmd.py`
- **test_non_deploy_command_does_not_load_any_provider()** (3 connections) — `cli/tests/test_deploy_cmd.py`
- **.bootstrap()** (2 connections) — `cli/tests/test_deploy_cmd.py`
- *... and 31 more nodes in this community*

## Relationships

- [CLI Run Entry Tests](CLI_Run_Entry_Tests.md) (18 shared connections)
- [CLI Main Entry](CLI_Main_Entry.md) (3 shared connections)
- [Deploy Provider Discovery](Deploy_Provider_Discovery.md) (2 shared connections)
- [Cloud Backend CLI Tests](Cloud_Backend_CLI_Tests.md) (1 shared connections)
- [Render & ReportStore Local](Render_%26_ReportStore_Local.md) (1 shared connections)

## Source Files

- `cli/gherkai_cli/__init__.py`
- `cli/tests/test_deploy_cmd.py`

## Audit Trail

- EXTRACTED: 130 (100%)
- INFERRED: 0 (0%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*