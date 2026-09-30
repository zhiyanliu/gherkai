# Composition Root Helpers

> 69 nodes · cohesion 0.05

## Key Concepts

- **test_compose.py** (128 connections) — `runtime/tests/test_compose.py`
- **resolve_worker_cmd()** (22 connections) — `runtime/gherkai_runtime/compose.py`
- **build_engines()** (20 connections) — `runtime/gherkai_runtime/compose.py`
- **Path** (8 connections)
- **resolve_region()** (8 connections) — `runtime/gherkai_runtime/compose.py`
- **Path** (8 connections)
- **load_feature()** (6 connections) — `runtime/gherkai_runtime/compose.py`
- **prune_empty_dirs()** (6 connections) — `runtime/gherkai_runtime/compose.py`
- **_fake_store_ctors()** (5 connections) — `runtime/tests/test_compose.py`
- **test_build_cloud_stores_builds_handles_when_not_injected()** (4 connections) — `runtime/tests/test_compose.py`
- **test_build_cloud_stores_uses_injected_handles_without_building_clients()** (4 connections) — `runtime/tests/test_compose.py`
- **test_build_engines_injects_steps_dir_env_both_legs()** (4 connections) — `runtime/tests/test_compose.py`
- **test_load_feature_uri_is_given_path_normalized()** (4 connections) — `runtime/tests/test_compose.py`
- **test_build_engines_injects_artifact_dirs_symmetrically()** (3 connections) — `runtime/tests/test_compose.py`
- **test_build_engines_injects_extra_http_headers_env()** (3 connections) — `runtime/tests/test_compose.py`
- **test_build_engines_miss_leg_does_not_break_the_other()** (3 connections) — `runtime/tests/test_compose.py`
- **test_build_engines_never_injects_artifact_s3_env()** (3 connections) — `runtime/tests/test_compose.py`
- **test_build_engines_region_profile_none_preserve_inherited()** (3 connections) — `runtime/tests/test_compose.py`
- **test_build_engines_region_profile_override_env()** (3 connections) — `runtime/tests/test_compose.py`
- **test_build_engines_scrubs_inherited_owned_env()** (3 connections) — `runtime/tests/test_compose.py`
- **test_chain_all_miss_raises_with_install_hint()** (3 connections) — `runtime/tests/test_compose.py`
- **test_chain_level1_env_cmd_wins_with_optional_cwd()** (3 connections) — `runtime/tests/test_compose.py`
- **test_chain_level1_unparsable_env_fails_loud()** (3 connections) — `runtime/tests/test_compose.py`
- **test_chain_level2_same_venv_module_no_wrapper()** (3 connections) — `runtime/tests/test_compose.py`
- **test_chain_level4_uvx_only_on_pure_release()** (3 connections) — `runtime/tests/test_compose.py`
- *... and 44 more nodes in this community*

## Relationships

- [Engine Capability Queries](Engine_Capability_Queries.md) (22 shared connections)
- [Cloud Resource Preflight](Cloud_Resource_Preflight.md) (19 shared connections)
- [Cloud Composition Helpers](Cloud_Composition_Helpers.md) (15 shared connections)
- [Version Skew Checking](Version_Skew_Checking.md) (13 shared connections)
- [AWS Target Resolution](AWS_Target_Resolution.md) (9 shared connections)
- [Version Stamp Skew Check](Version_Stamp_Skew_Check.md) (9 shared connections)
- [Worker Self-Describe Spawn](Worker_Self-Describe_Spawn.md) (4 shared connections)
- [Cloud Engine Resolver Build](Cloud_Engine_Resolver_Build.md) (3 shared connections)
- [CLI Test Fixtures](CLI_Test_Fixtures.md) (3 shared connections)
- [Task Def Stop Timeout](Task_Def_Stop_Timeout.md) (3 shared connections)
- [Plan and Scope Seam](Plan_and_Scope_Seam.md) (2 shared connections)
- [SSM Path Naming](SSM_Path_Naming.md) (2 shared connections)

## Source Files

- `runtime/gherkai_runtime/compose.py`
- `runtime/tests/test_compose.py`

## Audit Trail

- EXTRACTED: 222 (100%)
- INFERRED: 1 (0%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*