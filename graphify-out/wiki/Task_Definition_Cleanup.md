# Task Definition Cleanup

> 10 nodes · cohesion 0.20

## Key Concepts

- **_StubEcs** (10 connections) — `deploy_aws/tests/test_workers.py`
- **test_cleanup_deletes_an_old_orphan()** (6 connections) — `deploy_aws/tests/test_workers.py`
- **datetime** (3 connections)
- **.__init__()** (2 connections) — `deploy_aws/tests/test_workers.py`
- **最小 ECS 替身：**返回 `registeredAt`**（moto 不返回）——专供「孤儿满静默期后被回收」那一支。** (1 connections) — `deploy_aws/tests/test_workers.py`
- **孤儿的退休时刻 := 它的 `registeredAt`；早于静默期且无 run 引用 → 回收。** (1 connections) — `deploy_aws/tests/test_workers.py`
- **.delete_task_definitions()** (1 connections) — `deploy_aws/tests/test_workers.py`
- **.deregister_task_definition()** (1 connections) — `deploy_aws/tests/test_workers.py`
- **.describe_task_definition()** (1 connections) — `deploy_aws/tests/test_workers.py`
- **.list_task_definitions()** (1 connections) — `deploy_aws/tests/test_workers.py`

## Relationships

- [Container Push Tests](Container_Push_Tests.md) (6 shared connections)
- [Container Engine Adapter](Container_Engine_Adapter.md) (2 shared connections)
- [Worker Image Push Workflow](Worker_Image_Push_Workflow.md) (1 shared connections)

## Source Files

- `deploy_aws/tests/test_workers.py`

## Audit Trail

- EXTRACTED: 15 (83%)
- INFERRED: 3 (17%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*