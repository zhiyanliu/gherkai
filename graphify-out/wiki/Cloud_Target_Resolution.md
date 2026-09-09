# Cloud Target Resolution

> 63 nodes · cohesion 0.05

## Key Concepts

- **test_compose.py** (104 connections) — `runtime/tests/test_compose.py`
- **resolve_worker_cmd()** (22 connections) — `runtime/gherkai_runtime/compose.py`
- **_preflight_report_dir()** (11 connections) — `runtime/tests/test_compose.py`
- **resolve_cloud_target()** (10 connections) — `runtime/gherkai_runtime/compose.py`
- **resolve_network()** (9 connections) — `runtime/gherkai_runtime/compose.py`
- **resolve_region()** (9 connections) — `runtime/gherkai_runtime/compose.py`
- **engine_min_grace()** (6 connections) — `runtime/gherkai_runtime/compose.py`
- **_clear_aws_env()** (5 connections) — `runtime/tests/test_compose.py`
- **test_chain_level4_skipped_on_non_release_version()** (4 connections) — `runtime/tests/test_compose.py`
- **novaact_env_cmd()** (3 connections) — `runtime/tests/test_compose.py`
- **test_chain_all_miss_raises_with_install_hint()** (3 connections) — `runtime/tests/test_compose.py`
- **test_chain_level1_env_cmd_wins_with_optional_cwd()** (3 connections) — `runtime/tests/test_compose.py`
- **test_chain_level1_unparsable_env_fails_loud()** (3 connections) — `runtime/tests/test_compose.py`
- **test_chain_level2_same_venv_module_no_wrapper()** (3 connections) — `runtime/tests/test_compose.py`
- **test_chain_level4_uvx_only_on_pure_release()** (3 connections) — `runtime/tests/test_compose.py`
- **test_resolve_cloud_target_default_prefix_when_nothing_given()** (3 connections) — `runtime/tests/test_compose.py`
- **test_resolve_cloud_target_derives_all_names_from_prefix()** (3 connections) — `runtime/tests/test_compose.py`
- **test_resolve_cloud_target_env_fallbacks_are_deliberately_uneven()** (3 connections) — `runtime/tests/test_compose.py`
- **test_resolve_cloud_target_flags_win_over_env()** (3 connections) — `runtime/tests/test_compose.py`
- **midscene_env_cmd()** (2 connections) — `runtime/tests/test_compose.py`
- **fixture** (2 connections)
- **test_chain_level1_blank_env_falls_through()** (2 connections) — `runtime/tests/test_compose.py`
- **test_chain_level1_env_cmd_without_cwd_gives_none()** (2 connections) — `runtime/tests/test_compose.py`
- **test_chain_level2_skipped_when_module_missing()** (2 connections) — `runtime/tests/test_compose.py`
- **test_chain_level3_path_executable()** (2 connections) — `runtime/tests/test_compose.py`
- *... and 38 more nodes in this community*

## Relationships

- [Cloud Preflight Checks](Cloud_Preflight_Checks.md) (18 shared connections)
- [Engine Composition Helpers](Engine_Composition_Helpers.md) (16 shared connections)
- [SSM Path & Client Composition](SSM_Path_%26_Client_Composition.md) (11 shared connections)
- [Backend Version Stamp](Backend_Version_Stamp.md) (9 shared connections)
- [Store Composition & Step Query](Store_Composition_%26_Step_Query.md) (9 shared connections)
- [Version Skew Check](Version_Skew_Check.md) (8 shared connections)
- [S3 Report Store & Subprocess](S3_Report_Store_%26_Subprocess.md) (4 shared connections)
- [Runtime Naming Source](Runtime_Naming_Source.md) (2 shared connections)
- [Env Config & Error Classification](Env_Config_%26_Error_Classification.md) (2 shared connections)
- [Tunnel Host Watchdog](Tunnel_Host_Watchdog.md) (1 shared connections)
- [Local Run Store](Local_Run_Store.md) (1 shared connections)
- [CLI Main Entry](CLI_Main_Entry.md) (1 shared connections)

## Source Files

- `runtime/gherkai_runtime/compose.py`
- `runtime/tests/test_compose.py`

## Audit Trail

- EXTRACTED: 181 (99%)
- INFERRED: 2 (1%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*