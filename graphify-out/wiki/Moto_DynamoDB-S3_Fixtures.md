# Moto DynamoDB/S3 Fixtures

> 2 nodes · cohesion 1.00

## Key Concepts

- **aws()** (3 connections) — `core/tests/conftest.py`
- **在 moto mock 下建好 DDB 表 + S3 桶，产出 (boto3 resource/client, 名字) 供云端 adapter 测试注入。 表…** (1 connections) — `core/tests/conftest.py`

## Relationships

- [Test Fixtures And Env](Test_Fixtures_And_Env.md) (1 shared connections)
- [Cloud Adapter Test Fixtures](Cloud_Adapter_Test_Fixtures.md) (1 shared connections)

## Source Files

- `core/tests/conftest.py`

## Audit Trail

- EXTRACTED: 3 (100%)
- INFERRED: 0 (0%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*