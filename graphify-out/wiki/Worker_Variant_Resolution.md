# Worker Variant Resolution

> 45 nodes · cohesion 0.08

## Key Concepts

- **test_worker_variant.py** (31 connections) — `runtime/tests/test_worker_variant.py`
- **_seed()** (23 connections) — `runtime/tests/test_worker_variant.py`
- **_resolve()** (16 connections) — `runtime/tests/test_worker_variant.py`
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
- **worker variant 解析（ADR 0038「运行时与 preflight」）：variant 名 → 各引擎的 task-def revision…** (1 connections) — `runtime/tests/test_worker_variant.py`
- **不给 variant → 取部署级默认指针（ADR 0038「默认指针」）；解析结果带 digest 供打印。** (1 connections) — `runtime/tests/test_worker_variant.py`
- *... and 20 more nodes in this community*

## Relationships

- [Runtime Composition Root](Runtime_Composition_Root.md) (13 shared connections)
- [Resource Naming Source](Resource_Naming_Source.md) (7 shared connections)
- [Cloud Compose Helpers](Cloud_Compose_Helpers.md) (3 shared connections)
- [AWS Test Fixtures](AWS_Test_Fixtures.md) (2 shared connections)
- [Runtime Composition & Tunnel Host](Runtime_Composition_%26_Tunnel_Host.md) (1 shared connections)

## Source Files

- `runtime/tests/test_worker_variant.py`

## Audit Trail

- EXTRACTED: 103 (100%)
- INFERRED: 0 (0%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*