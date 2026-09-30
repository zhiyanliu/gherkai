# Resource Naming and Variants

> 53 nodes · cohesion 0.07

## Key Concepts

- **test_worker_variant.py** (31 connections) — `runtime/tests/test_worker_variant.py`
- **_seed()** (23 connections) — `runtime/tests/test_worker_variant.py`
- **_resolve()** (16 connections) — `runtime/tests/test_worker_variant.py`
- **worker_image_key()** (8 connections) — `runtime/gherkai_runtime/names.py`
- **test_digest_not_in_ecr_is_a_miss()** (8 connections) — `runtime/tests/test_worker_variant.py`
- **ecr_repo_name()** (7 connections) — `runtime/gherkai_runtime/names.py`
- **task_def_name()** (6 connections) — `runtime/gherkai_runtime/names.py`
- **_register_revision()** (6 connections) — `runtime/tests/test_worker_variant.py`
- **test_malformed_ssm_record_is_named()** (6 connections) — `runtime/tests/test_worker_variant.py`
- **_push_image()** (4 connections) — `runtime/tests/test_worker_variant.py`
- **test_default_task_defs_for_legacy_definition()** (4 connections) — `runtime/tests/test_worker_variant.py`
- **test_default_task_defs_missing_mapping_raises()** (4 connections) — `runtime/tests/test_worker_variant.py`
- **test_default_task_defs_missing_pointer_raises()** (4 connections) — `runtime/tests/test_worker_variant.py`
- **test_default_task_defs_no_backend_stamp_raises()** (4 connections) — `runtime/tests/test_worker_variant.py`
- **test_explicit_variant_ignores_default_pointer()** (4 connections) — `runtime/tests/test_worker_variant.py`
- **test_inactive_revision_is_a_miss()** (4 connections) — `runtime/tests/test_worker_variant.py`
- **test_invalid_variant_name_rejected_at_tag_layer()** (4 connections) — `runtime/tests/test_worker_variant.py`
- **test_missing_default_pointer_hints_deploy()** (4 connections) — `runtime/tests/test_worker_variant.py`
- **test_missing_mapping_hints_cli_upgrade_when_cli_older()** (4 connections) — `runtime/tests/test_worker_variant.py`
- **test_missing_mapping_hints_push_worker_when_same_version()** (4 connections) — `runtime/tests/test_worker_variant.py`
- **test_multi_engine_resolves_each()** (4 connections) — `runtime/tests/test_worker_variant.py`
- **test_never_falls_back_to_healthy_default_when_requested_variant_broken()** (4 connections) — `runtime/tests/test_worker_variant.py`
- **test_no_cli_version_fails_loud()** (4 connections) — `runtime/tests/test_worker_variant.py`
- **test_one_engine_missing_fails_whole_resolution()** (4 connections) — `runtime/tests/test_worker_variant.py`
- **test_unused_engine_not_probed()** (4 connections) — `runtime/tests/test_worker_variant.py`
- *... and 28 more nodes in this community*

## Relationships

- [Cloud Composition Helpers](Cloud_Composition_Helpers.md) (13 shared connections)
- [SSM Path Naming](SSM_Path_Naming.md) (9 shared connections)
- [Task Def Stop Timeout](Task_Def_Stop_Timeout.md) (2 shared connections)
- [CLI Test Fixtures](CLI_Test_Fixtures.md) (2 shared connections)
- [Cloud Engine Resolver Build](Cloud_Engine_Resolver_Build.md) (2 shared connections)
- [Composition Root Helpers](Composition_Root_Helpers.md) (1 shared connections)
- [Tunnel Host Orchestration](Tunnel_Host_Orchestration.md) (1 shared connections)

## Source Files

- `runtime/gherkai_runtime/names.py`
- `runtime/tests/test_compose.py`
- `runtime/tests/test_names_worker.py`
- `runtime/tests/test_worker_variant.py`

## Audit Trail

- EXTRACTED: 120 (100%)
- INFERRED: 0 (0%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*