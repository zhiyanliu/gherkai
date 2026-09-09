# Worker Command Resolution

> 36 nodes · cohesion 0.08

## Key Concepts

- **test_compose.py** (104 connections) — `runtime/tests/test_compose.py`
- **resolve_worker_cmd()** (22 connections) — `runtime/gherkai_runtime/compose.py`
- **engine_min_grace()** (6 connections) — `runtime/gherkai_runtime/compose.py`
- **test_chain_level4_skipped_on_non_release_version()** (4 connections) — `runtime/tests/test_compose.py`
- **_find_worker_spec()** (3 connections) — `runtime/gherkai_runtime/compose.py`
- **test_chain_all_miss_raises_with_install_hint()** (3 connections) — `runtime/tests/test_compose.py`
- **test_chain_level1_env_cmd_wins_with_optional_cwd()** (3 connections) — `runtime/tests/test_compose.py`
- **test_chain_level1_unparsable_env_fails_loud()** (3 connections) — `runtime/tests/test_compose.py`
- **test_chain_level2_same_venv_module_no_wrapper()** (3 connections) — `runtime/tests/test_compose.py`
- **test_chain_level4_uvx_only_on_pure_release()** (3 connections) — `runtime/tests/test_compose.py`
- **test_build_fargate_engines_per_engine_taskdef_and_region_no_profile()** (2 connections) — `runtime/tests/test_compose.py`
- **test_chain_level1_blank_env_falls_through()** (2 connections) — `runtime/tests/test_compose.py`
- **test_chain_level1_env_cmd_without_cwd_gives_none()** (2 connections) — `runtime/tests/test_compose.py`
- **test_chain_level2_skipped_when_module_missing()** (2 connections) — `runtime/tests/test_compose.py`
- **test_chain_level3_path_executable()** (2 connections) — `runtime/tests/test_compose.py`
- **test_chain_level4_skipped_when_launcher_absent()** (2 connections) — `runtime/tests/test_compose.py`
- **test_chain_novaact_miss_hint_is_python_side()** (2 connections) — `runtime/tests/test_compose.py`
- **test_engine_min_grace_midscene_nonzero_covers_onsignal_budget()** (2 connections) — `runtime/tests/test_compose.py`
- **test_engine_min_grace_mixed_run_takes_max()** (2 connections) — `runtime/tests/test_compose.py`
- **test_engine_min_grace_nova_covers_act_timeout_plus_margin()** (2 connections) — `runtime/tests/test_compose.py`
- **test_engine_min_grace_unknown_engine_zero()** (2 connections) — `runtime/tests/test_compose.py`
- **test_resolve_worker_cmd_unknown_engine()** (2 connections) — `runtime/tests/test_compose.py`
- **按四级定位链解析某引擎 worker 的拉起命令（ADR 0037 决策 3）。 1. env…** (1 connections) — `runtime/gherkai_runtime/compose.py`
- **`find_spec` 的容错壳：模块不在即 False，import 系统自身报错（坏 .pth / 半装）也当 miss、不击穿定位链。** (1 connections) — `runtime/gherkai_runtime/compose.py`
- **按引擎给 grace 下限（ADR 0024 grace 硬约束）——**引擎特定值住在组合根**（core 不认）。 Nova：`ACT_TIMEOUT_S…** (1 connections) — `runtime/gherkai_runtime/compose.py`
- *... and 11 more nodes in this community*

## Relationships

- [Cloud Resource Preflight Fakes](Cloud_Resource_Preflight_Fakes.md) (19 shared connections)
- [Engine Resolver Building](Engine_Resolver_Building.md) (16 shared connections)
- [Cloud Target Resolution](Cloud_Target_Resolution.md) (10 shared connections)
- [Backend Version Stamp Check](Backend_Version_Stamp_Check.md) (9 shared connections)
- [Local Stores & Deterministic Query](Local_Stores_%26_Deterministic_Query.md) (9 shared connections)
- [Version Skew Check](Version_Skew_Check.md) (8 shared connections)
- [Composition Root Wiring](Composition_Root_Wiring.md) (5 shared connections)
- [Fargate Network Resolution](Fargate_Network_Resolution.md) (4 shared connections)
- [S3 ReportStore & Subprocess Engine](S3_ReportStore_%26_Subprocess_Engine.md) (3 shared connections)
- [Worker Command Fixtures](Worker_Command_Fixtures.md) (2 shared connections)
- [CLI Main Entry](CLI_Main_Entry.md) (1 shared connections)
- [Environment and Version Resolution](Environment_and_Version_Resolution.md) (1 shared connections)

## Source Files

- `runtime/gherkai_runtime/compose.py`
- `runtime/tests/test_compose.py`

## Audit Trail

- EXTRACTED: 140 (99%)
- INFERRED: 2 (1%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*