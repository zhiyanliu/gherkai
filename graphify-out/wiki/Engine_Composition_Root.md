# Engine Composition Root

> 32 nodes · cohesion 0.07

## Key Concepts

- **build_engines()** (20 connections) — `runtime/gherkai_runtime/compose.py`
- **Path** (8 connections)
- **load_feature()** (6 connections) — `runtime/gherkai_runtime/compose.py`
- **make_resolver()** (5 connections) — `runtime/gherkai_runtime/compose.py`
- **scrubbed_environ()** (5 connections) — `runtime/gherkai_runtime/compose.py`
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
- **继承一份 os.environ、抹掉组合根拥有的那些键（见 `_COMPOSE_OWNED_WORKER_ENV`）——所有注入 env 的起手式。…** (1 connections) — `runtime/gherkai_runtime/compose.py`
- **每个引擎一个 SubprocessEngine（cmd 不同，core 引擎无关，ADR 0026）。 worker_log（ADR 0041…** (1 connections) — `runtime/gherkai_runtime/compose.py`
- *... and 7 more nodes in this community*

## Relationships

- [Worker Locator & AWS Resolution](Worker_Locator_%26_AWS_Resolution.md) (17 shared connections)
- [SSM Paths & Composition Root](SSM_Paths_%26_Composition_Root.md) (4 shared connections)
- [Worker Capability Query](Worker_Capability_Query.md) (3 shared connections)
- [Local Reconcile Rebuild](Local_Reconcile_Rebuild.md) (2 shared connections)
- [S3 Result Store Port](S3_Result_Store_Port.md) (2 shared connections)
- [Plan Job Generation](Plan_Job_Generation.md) (1 shared connections)
- [End-to-End Test Harness](End-to-End_Test_Harness.md) (1 shared connections)

## Source Files

- `runtime/gherkai_runtime/compose.py`
- `runtime/tests/test_compose.py`

## Audit Trail

- EXTRACTED: 66 (100%)
- INFERRED: 0 (0%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*