# AWS Target & Network Resolution

> 63 nodes · cohesion 0.05

## Key Concepts

- **test_compose.py** (128 connections) — `runtime/tests/test_compose.py`
- **check_version_skew()** (12 connections) — `runtime/gherkai_runtime/compose.py`
- **resolve_cloud_target()** (11 connections) — `runtime/gherkai_runtime/compose.py`
- **_preflight_report_dir()** (11 connections) — `runtime/tests/test_compose.py`
- **resolve_network()** (9 connections) — `runtime/gherkai_runtime/compose.py`
- **resolve_region()** (8 connections) — `runtime/gherkai_runtime/compose.py`
- **resolve_aws_identity()** (7 connections) — `runtime/gherkai_runtime/compose.py`
- **prune_empty_dirs()** (6 connections) — `runtime/gherkai_runtime/compose.py`
- **_clear_aws_env()** (5 connections) — `runtime/tests/test_compose.py`
- **_fake_store_ctors()** (5 connections) — `runtime/tests/test_compose.py`
- **test_build_cloud_stores_builds_handles_when_not_injected()** (4 connections) — `runtime/tests/test_compose.py`
- **test_build_cloud_stores_uses_injected_handles_without_building_clients()** (4 connections) — `runtime/tests/test_compose.py`
- **test_resolve_aws_identity_flag_wins_over_env()** (3 connections) — `runtime/tests/test_compose.py`
- **test_resolve_aws_identity_takes_profile_from_env()** (3 connections) — `runtime/tests/test_compose.py`
- **test_resolve_cloud_target_default_prefix_when_nothing_given()** (3 connections) — `runtime/tests/test_compose.py`
- **test_resolve_cloud_target_derives_all_names_from_prefix()** (3 connections) — `runtime/tests/test_compose.py`
- **test_resolve_cloud_target_env_fallbacks_are_deliberately_uneven()** (3 connections) — `runtime/tests/test_compose.py`
- **test_resolve_cloud_target_flags_win_over_env()** (3 connections) — `runtime/tests/test_compose.py`
- **test_resolve_cloud_target_goes_through_resolve_aws_identity()** (3 connections) — `runtime/tests/test_compose.py`
- **test_skew_block_when_cli_newer_names_both_exits()** (3 connections) — `runtime/tests/test_compose.py`
- **test_skew_cli_version_is_mandatory_no_runtime_fallback()** (3 connections) — `runtime/tests/test_compose.py`
- **test_skew_compares_release_segment_only()** (3 connections) — `runtime/tests/test_compose.py`
- **test_skew_skip_when_either_side_impure()** (3 connections) — `runtime/tests/test_compose.py`
- **test_skew_skip_when_own_version_unknown()** (3 connections) — `runtime/tests/test_compose.py`
- **test_skew_warn_when_stamp_missing_points_at_deploy()** (3 connections) — `runtime/tests/test_compose.py`
- *... and 38 more nodes in this community*

## Relationships

- [Worker Capability Queries](Worker_Capability_Queries.md) (19 shared connections)
- [Worker Command Resolution Chain](Worker_Command_Resolution_Chain.md) (18 shared connections)
- [Cloud Resource Preflight](Cloud_Resource_Preflight.md) (18 shared connections)
- [Engine Composition Helpers](Engine_Composition_Helpers.md) (17 shared connections)
- [Cloud Store Composition Root](Cloud_Store_Composition_Root.md) (14 shared connections)
- [Backend Version Skew Check](Backend_Version_Skew_Check.md) (10 shared connections)
- [Task Stop Timeout Read](Task_Stop_Timeout_Read.md) (4 shared connections)
- [Resource Naming Source](Resource_Naming_Source.md) (3 shared connections)
- [Test Fixtures & Conftest](Test_Fixtures_%26_Conftest.md) (3 shared connections)
- [Job/Scenario Explain Model](Job-Scenario_Explain_Model.md) (2 shared connections)
- [SQLite Event Log Adapter](SQLite_Event_Log_Adapter.md) (1 shared connections)
- [Tunnel Watch TTL Daemon](Tunnel_Watch_TTL_Daemon.md) (1 shared connections)

## Source Files

- `runtime/gherkai_runtime/compose.py`
- `runtime/tests/test_compose.py`

## Audit Trail

- EXTRACTED: 209 (100%)
- INFERRED: 1 (0%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*