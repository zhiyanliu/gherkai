# AWS Target Resolution

> 59 nodes · cohesion 0.05

## Key Concepts

- **test_compose.py** (128 connections) — `runtime/tests/test_compose.py`
- **resolve_worker_cmd()** (26 connections) — `runtime/gherkai_runtime/compose.py`
- **resolve_cloud_target()** (11 connections) — `runtime/gherkai_runtime/compose.py`
- **_preflight_report_dir()** (11 connections) — `runtime/tests/test_compose.py`
- **resolve_network()** (9 connections) — `runtime/gherkai_runtime/compose.py`
- **resolve_region()** (8 connections) — `runtime/gherkai_runtime/compose.py`
- **resolve_aws_identity()** (7 connections) — `runtime/gherkai_runtime/compose.py`
- **_clear_aws_env()** (5 connections) — `runtime/tests/test_compose.py`
- **test_chain_level4_skipped_on_non_release_version()** (4 connections) — `runtime/tests/test_compose.py`
- **test_chain_all_miss_raises_with_install_hint()** (3 connections) — `runtime/tests/test_compose.py`
- **test_chain_level1_env_cmd_wins_with_optional_cwd()** (3 connections) — `runtime/tests/test_compose.py`
- **test_chain_level1_unparsable_env_fails_loud()** (3 connections) — `runtime/tests/test_compose.py`
- **test_chain_level2_same_venv_module_no_wrapper()** (3 connections) — `runtime/tests/test_compose.py`
- **test_chain_level4_uvx_only_on_pure_release()** (3 connections) — `runtime/tests/test_compose.py`
- **test_resolve_aws_identity_flag_wins_over_env()** (3 connections) — `runtime/tests/test_compose.py`
- **test_resolve_aws_identity_takes_profile_from_env()** (3 connections) — `runtime/tests/test_compose.py`
- **test_resolve_cloud_target_default_prefix_when_nothing_given()** (3 connections) — `runtime/tests/test_compose.py`
- **test_resolve_cloud_target_derives_all_names_from_prefix()** (3 connections) — `runtime/tests/test_compose.py`
- **test_resolve_cloud_target_env_fallbacks_are_deliberately_uneven()** (3 connections) — `runtime/tests/test_compose.py`
- **test_resolve_cloud_target_flags_win_over_env()** (3 connections) — `runtime/tests/test_compose.py`
- **test_resolve_cloud_target_goes_through_resolve_aws_identity()** (3 connections) — `runtime/tests/test_compose.py`
- **parametrize** (2 connections)
- **test_chain_level1_blank_env_falls_through()** (2 connections) — `runtime/tests/test_compose.py`
- **test_chain_level1_env_cmd_without_cwd_gives_none()** (2 connections) — `runtime/tests/test_compose.py`
- **test_chain_level2_skipped_when_module_missing()** (2 connections) — `runtime/tests/test_compose.py`
- *... and 34 more nodes in this community*

## Relationships

- [Worker Capability Probing](Worker_Capability_Probing.md) (22 shared connections)
- [Local Compose Root](Local_Compose_Root.md) (18 shared connections)
- [Cloud Resource Preflight](Cloud_Resource_Preflight.md) (18 shared connections)
- [SSM Paths And Compose](SSM_Paths_And_Compose.md) (13 shared connections)
- [Version Skew Check](Version_Skew_Check.md) (13 shared connections)
- [Backend Version Skew Check](Backend_Version_Skew_Check.md) (9 shared connections)
- [Store Port Definitions](Store_Port_Definitions.md) (4 shared connections)
- [Cloud Compose Root](Cloud_Compose_Root.md) (4 shared connections)
- [Task Def Stop Timeout](Task_Def_Stop_Timeout.md) (4 shared connections)
- [Runtime Naming Source](Runtime_Naming_Source.md) (3 shared connections)
- [Worker Job Source Input](Worker_Job_Source_Input.md) (2 shared connections)
- [E2E Harness Script](E2E_Harness_Script.md) (2 shared connections)

## Source Files

- `runtime/gherkai_runtime/compose.py`
- `runtime/tests/test_compose.py`

## Audit Trail

- EXTRACTED: 210 (99%)
- INFERRED: 3 (1%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*