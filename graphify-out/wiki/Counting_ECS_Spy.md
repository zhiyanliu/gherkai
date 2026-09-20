# Counting ECS Spy

> 5 nodes · cohesion 0.40

## Key Concepts

- **CountingEcs** (9 connections) — `deploy_aws/tests/test_workers.py`
- **.describe_task_definition()** (1 connections) — `deploy_aws/tests/test_workers.py`
- **.__getattr__()** (1 connections) — `deploy_aws/tests/test_workers.py`
- **.__init__()** (1 connections) — `deploy_aws/tests/test_workers.py`
- **ECS client 的记参壳（数「同一个 task-def 被 describe 了几次」）——`Spy` 只记方法名，数不出这个。** (1 connections) — `deploy_aws/tests/test_workers.py`

## Relationships

- [Worker Image Tests](Worker_Image_Tests.md) (3 shared connections)
- [Container Engine Adapter](Container_Engine_Adapter.md) (2 shared connections)

## Source Files

- `deploy_aws/tests/test_workers.py`

## Audit Trail

- EXTRACTED: 7 (78%)
- INFERRED: 2 (22%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*