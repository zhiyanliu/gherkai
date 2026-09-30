# Deploy Command Frontend Tests

> 60 nodes · cohesion 0.06

## Key Concepts

- **test_deploy_cmd.py** (27 connections) — `cli/tests/test_deploy_cmd.py`
- **_StubProvider** (23 connections) — `cli/tests/test_deploy_cmd.py`
- **_FakeEP** (21 connections) — `cli/tests/test_deploy_cmd.py`
- **_patch_eps()** (21 connections) — `cli/tests/test_deploy_cmd.py`
- **gherkai_cli/__init__.py** (7 connections) — `cli/gherkai_cli/__init__.py`
- **test_cli_version_is_handed_to_provider()** (7 connections) — `cli/tests/test_deploy_cmd.py`
- **test_dispatch_maps_command_face_to_provider_method()** (7 connections) — `cli/tests/test_deploy_cmd.py`
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
- **test_provider_init_failure_is_named_not_traceback()** (5 connections) — `cli/tests/test_deploy_cmd.py`
- **test_provider_load_failure_is_named_not_traceback()** (5 connections) — `cli/tests/test_deploy_cmd.py`
- **test_provider_subverb_seam_takes_precedence()** (5 connections) — `cli/tests/test_deploy_cmd.py`
- **test_readonly_flags_cannot_be_combined_with_a_provider_subverb()** (5 connections) — `cli/tests/test_deploy_cmd.py`
- **test_unknown_provider_name_lists_installed()** (5 connections) — `cli/tests/test_deploy_cmd.py`
- **test_help_works_without_provider_and_explains_why()** (4 connections) — `cli/tests/test_deploy_cmd.py`
- **test_zero_providers_points_at_the_extra()** (4 connections) — `cli/tests/test_deploy_cmd.py`
- *... and 35 more nodes in this community*

## Relationships

- [Plan Command CLI Tests](Plan_Command_CLI_Tests.md) (20 shared connections)
- [CLI Command Entrypoints](CLI_Command_Entrypoints.md) (2 shared connections)
- [Deploy Provider Discovery](Deploy_Provider_Discovery.md) (2 shared connections)
- [Engine Listing and JSON Contract](Engine_Listing_and_JSON_Contract.md) (1 shared connections)
- [CLI Run Wiring Tests](CLI_Run_Wiring_Tests.md) (1 shared connections)
- [Result Tree Text Rendering](Result_Tree_Text_Rendering.md) (1 shared connections)
- [Skill Docs Guardrail Tests](Skill_Docs_Guardrail_Tests.md) (1 shared connections)

## Source Files

- `cli/gherkai_cli/__init__.py`
- `cli/tests/test_deploy_cmd.py`

## Audit Trail

- EXTRACTED: 141 (100%)
- INFERRED: 0 (0%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*