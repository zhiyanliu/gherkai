# AWS Test Fixtures (moto)

> 5 nodes · cohesion 0.40

## Key Concepts

- **aws()** (3 connections) — `runtime/tests/test_worker_variant.py`
- **_fake_aws_creds()** (3 connections) — `runtime/tests/test_worker_variant.py`
- **fixture** (2 connections)
- **硬隔离：假凭证 + 固定 region，绝不误连真 AWS（同 core/tests/conftest.py 的套装）。** (1 connections) — `runtime/tests/test_worker_variant.py`
- **moto 下的 ssm / ecs / ecr 三个 client（本 ADR 解析路径要读的全部 AWS 面）。** (1 connections) — `runtime/tests/test_worker_variant.py`

## Relationships

- [Worker Variant Resolution](Worker_Variant_Resolution.md) (2 shared connections)

## Source Files

- `runtime/tests/test_worker_variant.py`

## Audit Trail

- EXTRACTED: 6 (100%)
- INFERRED: 0 (0%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*