# Task Definition Cleanup Stub

> 9 nodes · cohesion 0.22

## Key Concepts

- **_StubEcs** (10 connections) — `deploy_aws/tests/test_workers.py`
- **test_cleanup_deletes_an_old_orphan()** (6 connections) — `deploy_aws/tests/test_workers.py`
- **.__init__()** (2 connections) — `deploy_aws/tests/test_workers.py`
- **最小 ECS 替身：**返回 `registeredAt`**（moto 不返回）——专供「孤儿满静默期后被回收」那一支。** (1 connections) — `deploy_aws/tests/test_workers.py`
- **孤儿的退休时刻 := 它的 `registeredAt`；早于静默期且无 run 引用 → 回收。** (1 connections) — `deploy_aws/tests/test_workers.py`
- **.delete_task_definitions()** (1 connections) — `deploy_aws/tests/test_workers.py`
- **.deregister_task_definition()** (1 connections) — `deploy_aws/tests/test_workers.py`
- **.describe_task_definition()** (1 connections) — `deploy_aws/tests/test_workers.py`
- **.list_task_definitions()** (1 connections) — `deploy_aws/tests/test_workers.py`

## Relationships

- [Container Worker Tests](Container_Worker_Tests.md) (5 shared connections)
- [Container Engine Adapter](Container_Engine_Adapter.md) (2 shared connections)
- [Worker Image Management](Worker_Image_Management.md) (1 shared connections)

## Source Files

- `deploy_aws/tests/test_workers.py`

## Audit Trail

- EXTRACTED: 13 (81%)
- INFERRED: 3 (19%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*