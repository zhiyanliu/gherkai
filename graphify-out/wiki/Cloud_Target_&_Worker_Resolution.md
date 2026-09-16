# Cloud Target & Worker Resolution

> 68 nodes · cohesion 0.04

## Key Concepts

- **test_compose.py** (112 connections) — `runtime/tests/test_compose.py`
- **resolve_worker_cmd()** (23 connections) — `runtime/gherkai_runtime/compose.py`
- **resolve_cloud_target()** (10 connections) — `runtime/gherkai_runtime/compose.py`
- **resolve_network()** (9 connections) — `runtime/gherkai_runtime/compose.py`
- **resolve_region()** (9 connections) — `runtime/gherkai_runtime/compose.py`
- **engine_min_grace()** (6 connections) — `runtime/gherkai_runtime/compose.py`
- **prune_empty_dirs()** (6 connections) — `runtime/gherkai_runtime/compose.py`
- **_clear_aws_env()** (5 connections) — `runtime/tests/test_compose.py`
- **_fake_store_ctors()** (5 connections) — `runtime/tests/test_compose.py`
- **_runtime_version()** (4 connections) — `runtime/gherkai_runtime/compose.py`
- **test_build_cloud_stores_builds_handles_when_not_injected()** (4 connections) — `runtime/tests/test_compose.py`
- **test_build_cloud_stores_uses_injected_handles_without_building_clients()** (4 connections) — `runtime/tests/test_compose.py`
- **test_chain_level4_skipped_on_non_release_version()** (4 connections) — `runtime/tests/test_compose.py`
- **_find_worker_spec()** (3 connections) — `runtime/gherkai_runtime/compose.py`
- **test_chain_all_miss_raises_with_install_hint()** (3 connections) — `runtime/tests/test_compose.py`
- **test_chain_level1_env_cmd_wins_with_optional_cwd()** (3 connections) — `runtime/tests/test_compose.py`
- **test_chain_level1_unparsable_env_fails_loud()** (3 connections) — `runtime/tests/test_compose.py`
- **test_chain_level2_same_venv_module_no_wrapper()** (3 connections) — `runtime/tests/test_compose.py`
- **test_chain_level4_uvx_only_on_pure_release()** (3 connections) — `runtime/tests/test_compose.py`
- **test_resolve_cloud_target_default_prefix_when_nothing_given()** (3 connections) — `runtime/tests/test_compose.py`
- **test_resolve_cloud_target_derives_all_names_from_prefix()** (3 connections) — `runtime/tests/test_compose.py`
- **test_resolve_cloud_target_env_fallbacks_are_deliberately_uneven()** (3 connections) — `runtime/tests/test_compose.py`
- **test_resolve_cloud_target_flags_win_over_env()** (3 connections) — `runtime/tests/test_compose.py`
- **test_chain_level1_blank_env_falls_through()** (2 connections) — `runtime/tests/test_compose.py`
- **test_chain_level1_env_cmd_without_cwd_gives_none()** (2 connections) — `runtime/tests/test_compose.py`
- *... and 43 more nodes in this community*

## Relationships

- [Cloud Resource Preflight](Cloud_Resource_Preflight.md) (19 shared connections)
- [Engine Composition Helpers](Engine_Composition_Helpers.md) (17 shared connections)
- [Runtime Composition Root](Runtime_Composition_Root.md) (13 shared connections)
- [Backend Version Skew Check](Backend_Version_Skew_Check.md) (9 shared connections)
- [Version Skew Check](Version_Skew_Check.md) (8 shared connections)
- [Deterministic Step Query](Deterministic_Step_Query.md) (7 shared connections)
- [Version Release Comparison](Version_Release_Comparison.md) (5 shared connections)
- [S3 Report Store & Control Plane](S3_Report_Store_%26_Control_Plane.md) (4 shared connections)
- [Backend CDK Stack](Backend_CDK_Stack.md) (2 shared connections)
- [AWS Test Fixtures](AWS_Test_Fixtures.md) (2 shared connections)
- [Job Explain & S3 Offload](Job_Explain_%26_S3_Offload.md) (2 shared connections)
- [Resource Naming Source](Resource_Naming_Source.md) (1 shared connections)

## Source Files

- `runtime/gherkai_runtime/compose.py`
- `runtime/tests/test_compose.py`

## Audit Trail

- EXTRACTED: 194 (98%)
- INFERRED: 4 (2%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*