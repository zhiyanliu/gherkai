# Worker Locator & AWS Resolution

> 71 nodes · cohesion 0.04

## Key Concepts

- **test_compose.py** (128 connections) — `runtime/tests/test_compose.py`
- **resolve_worker_cmd()** (23 connections) — `runtime/gherkai_runtime/compose.py`
- **resolve_cloud_target()** (11 connections) — `runtime/gherkai_runtime/compose.py`
- **_preflight_report_dir()** (11 connections) — `runtime/tests/test_compose.py`
- **resolve_network()** (9 connections) — `runtime/gherkai_runtime/compose.py`
- **resolve_region()** (8 connections) — `runtime/gherkai_runtime/compose.py`
- **resolve_aws_identity()** (7 connections) — `runtime/gherkai_runtime/compose.py`
- **prune_empty_dirs()** (6 connections) — `runtime/gherkai_runtime/compose.py`
- **_clear_aws_env()** (5 connections) — `runtime/tests/test_compose.py`
- **_fake_store_ctors()** (5 connections) — `runtime/tests/test_compose.py`
- **_runtime_version()** (4 connections) — `runtime/gherkai_runtime/compose.py`
- **test_build_cloud_stores_builds_handles_when_not_injected()** (4 connections) — `runtime/tests/test_compose.py`
- **test_build_cloud_stores_uses_injected_handles_without_building_clients()** (4 connections) — `runtime/tests/test_compose.py`
- **_find_worker_spec()** (3 connections) — `runtime/gherkai_runtime/compose.py`
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
- *... and 46 more nodes in this community*

## Relationships

- [Worker Capability Query](Worker_Capability_Query.md) (22 shared connections)
- [Cloud Resource Preflight](Cloud_Resource_Preflight.md) (18 shared connections)
- [Engine Composition Root](Engine_Composition_Root.md) (17 shared connections)
- [SSM Paths & Composition Root](SSM_Paths_%26_Composition_Root.md) (14 shared connections)
- [Version Skew Checking](Version_Skew_Checking.md) (13 shared connections)
- [Backend Version Skew Check](Backend_Version_Skew_Check.md) (9 shared connections)
- [Resource Naming Source](Resource_Naming_Source.md) (3 shared connections)
- [S3 Report Store](S3_Report_Store.md) (3 shared connections)
- [AWS Test Fixtures (moto)](AWS_Test_Fixtures_%28moto%29.md) (3 shared connections)
- [Task Def Stop Timeout](Task_Def_Stop_Timeout.md) (3 shared connections)
- [Backend CDK Stack](Backend_CDK_Stack.md) (2 shared connections)
- [Run Metadata & S3 Offload](Run_Metadata_%26_S3_Offload.md) (2 shared connections)

## Source Files

- `runtime/gherkai_runtime/compose.py`
- `runtime/tests/test_compose.py`

## Audit Trail

- EXTRACTED: 223 (99%)
- INFERRED: 3 (1%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*