# Worker Variant Resolution

> 52 nodes · cohesion 0.07

## Key Concepts

- **test_worker_variant.py** (31 connections) — `runtime/tests/test_worker_variant.py`
- **_seed()** (23 connections) — `runtime/tests/test_worker_variant.py`
- **_resolve()** (16 connections) — `runtime/tests/test_worker_variant.py`
- **worker_image_key()** (8 connections) — `runtime/gherkai_runtime/names.py`
- **test_digest_not_in_ecr_is_a_miss()** (8 connections) — `runtime/tests/test_worker_variant.py`
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
- **test_variant_none_uses_default_pointer()** (4 connections) — `runtime/tests/test_worker_variant.py`
- **aws()** (3 connections) — `runtime/tests/test_worker_variant.py`
- *... and 27 more nodes in this community*

## Relationships

- [SSM Path & Client Composition](SSM_Path_%26_Client_Composition.md) (12 shared connections)
- [Runtime Naming Source](Runtime_Naming_Source.md) (10 shared connections)
- [Cloud Store Composition](Cloud_Store_Composition.md) (3 shared connections)

## Source Files

- `runtime/gherkai_runtime/names.py`
- `runtime/tests/test_worker_variant.py`

## Audit Trail

- EXTRACTED: 112 (100%)
- INFERRED: 0 (0%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*