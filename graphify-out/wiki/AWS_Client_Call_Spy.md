# AWS Client Call Spy

> 4 nodes · cohesion 0.50

## Key Concepts

- **Spy** (7 connections) — `deploy_aws/tests/test_workers.py`
- **boto3 client 的记名壳（验「这一步之前一次 AWS 都没调」）。** (1 connections) — `deploy_aws/tests/test_workers.py`
- **.__getattr__()** (1 connections) — `deploy_aws/tests/test_workers.py`
- **.__init__()** (1 connections) — `deploy_aws/tests/test_workers.py`

## Relationships

- [Container Worker Push Tests](Container_Worker_Push_Tests.md) (2 shared connections)
- [Container Engine Adapter](Container_Engine_Adapter.md) (2 shared connections)

## Source Files

- `deploy_aws/tests/test_workers.py`

## Audit Trail

- EXTRACTED: 5 (71%)
- INFERRED: 2 (29%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*