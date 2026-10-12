# Moto SSM/ECS/ECR Clients

> 2 nodes · cohesion 1.00

## Key Concepts

- **aws()** (3 connections) — `runtime/tests/test_worker_variant.py`
- **moto 下的 ssm / ecs / ecr 三个 client（本 ADR 解析路径要读的全部 AWS 面）。** (1 connections) — `runtime/tests/test_worker_variant.py`

## Relationships

- [Test Fixtures And Env](Test_Fixtures_And_Env.md) (1 shared connections)
- [Worker Variant Resolution](Worker_Variant_Resolution.md) (1 shared connections)

## Source Files

- `runtime/tests/test_worker_variant.py`

## Audit Trail

- EXTRACTED: 3 (100%)
- INFERRED: 0 (0%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*