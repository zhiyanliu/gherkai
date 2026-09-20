# Fail-Loud Config Validation

> 2 nodes · cohesion 1.00

## Key Concepts

- **test_bucket_without_logs_dir_fails_loud()** (2 connections) — `engines/novaact/tests/test_artifact_upload.py`
- **半注入(有桶缺 NOVA_LOGS_DIR)→ 装配矛盾 fail-loud(静默 no-op 会让产物随容器盘销毁必丢,ADR 0033)。** (1 connections) — `engines/novaact/tests/test_artifact_upload.py`

## Relationships

- [Artifact Upload Tests](Artifact_Upload_Tests.md) (1 shared connections)

## Source Files

- `engines/novaact/tests/test_artifact_upload.py`

## Audit Trail

- EXTRACTED: 2 (100%)
- INFERRED: 0 (0%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*