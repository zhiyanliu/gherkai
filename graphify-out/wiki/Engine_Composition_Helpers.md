# Engine Composition Helpers

> 28 nodes · cohesion 0.08

## Key Concepts

- **build_engines()** (18 connections) — `runtime/gherkai_runtime/compose.py`
- **Path** (8 connections)
- **load_feature()** (6 connections) — `runtime/gherkai_runtime/compose.py`
- **make_resolver()** (5 connections) — `runtime/gherkai_runtime/compose.py`
- **test_build_engines_injects_steps_dir_env_both_legs()** (4 connections) — `runtime/tests/test_compose.py`
- **test_load_feature_uri_is_given_path_normalized()** (4 connections) — `runtime/tests/test_compose.py`
- **test_build_engines_injects_artifact_dirs_symmetrically()** (3 connections) — `runtime/tests/test_compose.py`
- **test_build_engines_injects_extra_http_headers_env()** (3 connections) — `runtime/tests/test_compose.py`
- **test_build_engines_miss_leg_does_not_break_the_other()** (3 connections) — `runtime/tests/test_compose.py`
- **test_build_engines_never_injects_artifact_s3_env()** (3 connections) — `runtime/tests/test_compose.py`
- **test_build_engines_region_profile_none_preserve_inherited()** (3 connections) — `runtime/tests/test_compose.py`
- **test_build_engines_region_profile_override_env()** (3 connections) — `runtime/tests/test_compose.py`
- **test_load_feature_absolute_path_stays_absolute()** (3 connections) — `runtime/tests/test_compose.py`
- **test_no_repo_root_consumer_remains()** (3 connections) — `runtime/tests/test_compose.py`
- **test_resolver_known_and_unknown()** (3 connections) — `runtime/tests/test_compose.py`
- **test_build_engines_has_both_legs()** (2 connections) — `runtime/tests/test_compose.py`
- **test_build_engines_midscene_no_rebuild_when_no_region_profile()** (2 connections) — `runtime/tests/test_compose.py`
- **test_build_engines_no_dirs_midscene_env_none()** (2 connections) — `runtime/tests/test_compose.py`
- **test_build_engines_nova_always_has_act_timeout()** (2 connections) — `runtime/tests/test_compose.py`
- **test_build_engines_region_profile_injected_on_rebuild_path_both_legs()** (2 connections) — `runtime/tests/test_compose.py`
- **读 .feature 文件 → core 要的 FeatureSource（uri+text）。 core 不碰文件系统（ADR 0025）：读文件、推导…** (1 connections) — `runtime/gherkai_runtime/compose.py`
- **每个引擎一个 SubprocessEngine（cmd 不同，core 引擎无关，ADR 0026）。 no_artifacts（`--no-…** (1 connections) — `runtime/gherkai_runtime/compose.py`
- **dict → core 要的 EngineResolver（按 job.engine 取 Engine；未知引擎报错）。** (1 connections) — `runtime/gherkai_runtime/compose.py`
- **某引擎定位链 miss **不连坐**另一条腿（ADR 0037 决策 3）：dev 下 midscene 未装是常态， novaact-only 的 run…** (1 connections) — `runtime/tests/test_compose.py`
- **extra_http_headers（ADR 0035 决策 4）→ 两 worker env 注…** (1 connections) — `runtime/tests/test_compose.py`
- *... and 3 more nodes in this community*

## Relationships

- [Cloud Target Resolution](Cloud_Target_Resolution.md) (16 shared connections)
- [SSM Path & Client Composition](SSM_Path_%26_Client_Composition.md) (3 shared connections)
- [Local Run Store](Local_Run_Store.md) (2 shared connections)
- [Run Result Rendering](Run_Result_Rendering.md) (2 shared connections)
- [Store Composition & Step Query](Store_Composition_%26_Step_Query.md) (2 shared connections)
- [Feature Planning](Feature_Planning.md) (1 shared connections)

## Source Files

- `runtime/gherkai_runtime/compose.py`
- `runtime/tests/test_compose.py`

## Audit Trail

- EXTRACTED: 58 (100%)
- INFERRED: 0 (0%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*