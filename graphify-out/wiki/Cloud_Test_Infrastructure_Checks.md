# Cloud Test Infrastructure Checks

> 5 nodes · cohesion 0.40

## Key Concepts

- **test_cloud_infra.py** (4 connections) — `core/tests/test_cloud_infra.py`
- **步骤 0 自检（ADR 0030 决定六）：moto 测试基建可用 + 硬隔离生效。 在写任何云端 adapter 前，先证明 conftest 的…** (1 connections) — `core/tests/test_cloud_infra.py`
- **test_ddb_native_map_single_element_update()** (1 connections) — `core/tests/test_cloud_infra.py`
- **test_ddb_table_and_s3_bucket_ready()** (1 connections) — `core/tests/test_cloud_infra.py`
- **test_fake_creds_hard_isolation()** (1 connections) — `core/tests/test_cloud_infra.py`

## Relationships

- No strong cross-community connections detected

## Source Files

- `core/tests/test_cloud_infra.py`

## Audit Trail

- EXTRACTED: 4 (100%)
- INFERRED: 0 (0%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*