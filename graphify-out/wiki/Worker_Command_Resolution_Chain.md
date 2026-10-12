# Worker Command Resolution Chain

> 40 nodes · cohesion 0.05

## Key Concepts

- **resolve_worker_cmd()** (26 connections) — `runtime/gherkai_runtime/compose.py`
- **_release_cmp()** (6 connections) — `runtime/gherkai_runtime/compose.py`
- **_variant_miss_hint()** (6 connections) — `runtime/gherkai_runtime/compose.py`
- **is_pure_release()** (5 connections) — `runtime/gherkai_runtime/compose.py`
- **_runtime_version()** (4 connections) — `runtime/gherkai_runtime/compose.py`
- **test_chain_level4_skipped_on_non_release_version()** (4 connections) — `runtime/tests/test_compose.py`
- **_find_worker_spec()** (3 connections) — `runtime/gherkai_runtime/compose.py`
- **_release_key()** (3 connections) — `runtime/gherkai_runtime/compose.py`
- **test_chain_all_miss_raises_with_install_hint()** (3 connections) — `runtime/tests/test_compose.py`
- **test_chain_level1_env_cmd_wins_with_optional_cwd()** (3 connections) — `runtime/tests/test_compose.py`
- **test_chain_level1_unparsable_env_fails_loud()** (3 connections) — `runtime/tests/test_compose.py`
- **test_chain_level2_same_venv_module_no_wrapper()** (3 connections) — `runtime/tests/test_compose.py`
- **test_chain_level4_uvx_only_on_pure_release()** (3 connections) — `runtime/tests/test_compose.py`
- **test_variant_miss_hint_offers_push_and_base_fallback()** (3 connections) — `runtime/tests/test_compose.py`
- **test_variant_miss_hint_older_cli_only_guides_upgrade()** (3 connections) — `runtime/tests/test_compose.py`
- **e2e_harness.py（opt-in 手动端到端验证脚本）** (3 connections) — `tools/e2e_harness.md`
- **parametrize** (2 connections)
- **test_chain_level1_blank_env_falls_through()** (2 connections) — `runtime/tests/test_compose.py`
- **test_chain_level1_env_cmd_without_cwd_gives_none()** (2 connections) — `runtime/tests/test_compose.py`
- **test_chain_level2_skipped_when_module_missing()** (2 connections) — `runtime/tests/test_compose.py`
- **test_chain_level3_path_executable()** (2 connections) — `runtime/tests/test_compose.py`
- **test_chain_level4_skipped_when_launcher_absent()** (2 connections) — `runtime/tests/test_compose.py`
- **test_chain_novaact_miss_hint_is_python_side()** (2 connections) — `runtime/tests/test_compose.py`
- **test_pure_release_predicate()** (2 connections) — `runtime/tests/test_compose.py`
- **test_resolve_worker_cmd_unknown_engine()** (2 connections) — `runtime/tests/test_compose.py`
- *... and 15 more nodes in this community*

## Relationships

- [AWS Target & Network Resolution](AWS_Target_%26_Network_Resolution.md) (18 shared connections)
- [Cloud Store Composition Root](Cloud_Store_Composition_Root.md) (7 shared connections)
- [Cloud Launcher & Fargate Adapters](Cloud_Launcher_%26_Fargate_Adapters.md) (2 shared connections)
- [E2E Interrupt Harness](E2E_Interrupt_Harness.md) (2 shared connections)
- [Worker Capability Queries](Worker_Capability_Queries.md) (2 shared connections)
- [Worker Job Source Input](Worker_Job_Source_Input.md) (1 shared connections)
- [Core Library Concepts & ADRs](Core_Library_Concepts_%26_ADRs.md) (1 shared connections)
- [Engine Composition Helpers](Engine_Composition_Helpers.md) (1 shared connections)
- [Deploy CLI Provider Discovery](Deploy_CLI_Provider_Discovery.md) (1 shared connections)
- [Feature Parsing & Errors](Feature_Parsing_%26_Errors.md) (1 shared connections)

## Source Files

- `runtime/gherkai_runtime/compose.py`
- `runtime/tests/test_compose.py`
- `tools/e2e_harness.md`

## Audit Trail

- EXTRACTED: 71 (95%)
- INFERRED: 4 (5%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*