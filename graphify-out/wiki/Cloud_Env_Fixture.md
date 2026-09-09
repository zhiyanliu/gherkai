# Cloud Env Fixture

> 3 nodes · cohesion 0.67

## Key Concepts

- **cloud_env()** (3 connections) — `deploy_aws/tests/test_lambda_handlers.py`
- **fixture** (1 connections)
- **moto 内存 runs/events 表 + 桶 + 推进器 Lambda 的 env（先盖假凭证、再 mock，绝不连真 AWS）。** (1 connections) — `deploy_aws/tests/test_lambda_handlers.py`

## Relationships

- [Lambda Handler Tests](Lambda_Handler_Tests.md) (1 shared connections)

## Source Files

- `deploy_aws/tests/test_lambda_handlers.py`

## Audit Trail

- EXTRACTED: 3 (100%)
- INFERRED: 0 (0%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*