# Engine Composition Helpers

> 31 nodes · cohesion 0.08

## Key Concepts

- **build_engines()** (23 connections) — `runtime/gherkai_runtime/compose.py`
- **Path** (8 connections)
- **load_feature()** (7 connections) — `runtime/gherkai_runtime/compose.py`
- **make_resolver()** (7 connections) — `runtime/gherkai_runtime/compose.py`
- **gherkai-runtime README (PyPI 入口页)** (4 connections) — `runtime/README.md`
- **test_build_engines_injects_steps_dir_env_both_legs()** (4 connections) — `runtime/tests/test_compose.py`
- **test_load_feature_uri_is_given_path_normalized()** (4 connections) — `runtime/tests/test_compose.py`
- **test_build_engines_injects_artifact_dirs_symmetrically()** (3 connections) — `runtime/tests/test_compose.py`
- **test_build_engines_injects_extra_http_headers_env()** (3 connections) — `runtime/tests/test_compose.py`
- **test_build_engines_miss_leg_does_not_break_the_other()** (3 connections) — `runtime/tests/test_compose.py`
- **test_build_engines_never_injects_artifact_s3_env()** (3 connections) — `runtime/tests/test_compose.py`
- **test_build_engines_region_profile_none_preserve_inherited()** (3 connections) — `runtime/tests/test_compose.py`
- **test_build_engines_region_profile_override_env()** (3 connections) — `runtime/tests/test_compose.py`
- **test_build_engines_scrubs_inherited_owned_env()** (3 connections) — `runtime/tests/test_compose.py`
- **test_load_feature_absolute_path_stays_absolute()** (3 connections) — `runtime/tests/test_compose.py`
- **test_no_repo_root_consumer_remains()** (3 connections) — `runtime/tests/test_compose.py`
- **test_resolver_known_and_unknown()** (3 connections) — `runtime/tests/test_compose.py`
- **test_build_engines_has_both_legs()** (2 connections) — `runtime/tests/test_compose.py`
- **test_build_engines_midscene_no_rebuild_when_no_region_profile()** (2 connections) — `runtime/tests/test_compose.py`
- **test_build_engines_no_dirs_midscene_env_none()** (2 connections) — `runtime/tests/test_compose.py`
- **test_build_engines_nova_always_has_act_timeout()** (2 connections) — `runtime/tests/test_compose.py`
- **test_build_engines_region_profile_injected_on_rebuild_path_both_legs()** (2 connections) — `runtime/tests/test_compose.py`
- **读 .feature 文件 → core 要的 FeatureSource（uri+text）。 core 不碰文件系统（ADR 0025）：读文件、推导…** (1 connections) — `runtime/gherkai_runtime/compose.py`
- **每个引擎一个 SubprocessEngine（cmd 不同，core 引擎无关，ADR 0026）。 worker_log（ADR 0041…** (1 connections) — `runtime/gherkai_runtime/compose.py`
- **dict → core 要的 EngineResolver（按 job.engine 取 Engine；未知引擎报错）。** (1 connections) — `runtime/gherkai_runtime/compose.py`
- *... and 6 more nodes in this community*

## Relationships

- [AWS Target & Network Resolution](AWS_Target_%26_Network_Resolution.md) (17 shared connections)
- [Cloud Store Composition Root](Cloud_Store_Composition_Root.md) (3 shared connections)
- [SQLite Event Log Adapter](SQLite_Event_Log_Adapter.md) (2 shared connections)
- [Cloud Launcher & Fargate Adapters](Cloud_Launcher_%26_Fargate_Adapters.md) (2 shared connections)
- [Worker Capability Queries](Worker_Capability_Queries.md) (2 shared connections)
- [E2E Interrupt Harness](E2E_Interrupt_Harness.md) (1 shared connections)
- [Worker Command Resolution Chain](Worker_Command_Resolution_Chain.md) (1 shared connections)
- [Feature Parsing & Errors](Feature_Parsing_%26_Errors.md) (1 shared connections)
- [Core Library Concepts & ADRs](Core_Library_Concepts_%26_ADRs.md) (1 shared connections)

## Source Files

- `runtime/README.md`
- `runtime/gherkai_runtime/compose.py`
- `runtime/tests/test_compose.py`

## Audit Trail

- EXTRACTED: 67 (99%)
- INFERRED: 1 (1%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*