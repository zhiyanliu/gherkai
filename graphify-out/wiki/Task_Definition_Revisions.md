# Task Definition Revisions

> 16 nodes · cohesion 0.12

## Key Concepts

- **_StubEcs** (10 connections) — `deploy_aws/tests/test_workers.py`
- **RevisionInfo** (8 connections) — `deploy_aws/gherkai_deploy_aws/workers.py`
- **test_cleanup_deletes_an_old_orphan()** (6 connections) — `deploy_aws/tests/test_workers.py`
- **test_pending_cleanup_is_json_serializable_with_real_registered_at()** (5 connections) — `deploy_aws/tests/test_workers.py`
- **datetime** (4 connections)
- **.has_lineage()** (2 connections) — `deploy_aws/gherkai_deploy_aws/workers.py`
- **.__init__()** (2 connections) — `deploy_aws/tests/test_workers.py`
- **family 里的一个 ACTIVE revision + 它的 tags。** (1 connections) — `deploy_aws/gherkai_deploy_aws/workers.py`
- **带血缘 tags 吗？—— **模板 revision 与任何手工注册的 revision 都没有**，故它们永不进清理候选。** (1 connections) — `deploy_aws/gherkai_deploy_aws/workers.py`
- **最小 ECS 替身：**返回 `registeredAt`**（moto 不返回）——专供「孤儿满静默期后被回收」那一支。** (1 connections) — `deploy_aws/tests/test_workers.py`
- **孤儿的退休时刻取它的 `registeredAt`；早于静默期且无 run 引用 → 回收。** (1 connections) — `deploy_aws/tests/test_workers.py`
- **真 AWS 的 DescribeTaskDefinition 带 registeredAt（datetime），moto 不带——`--json` 曾因此…** (1 connections) — `deploy_aws/tests/test_workers.py`
- **.delete_task_definitions()** (1 connections) — `deploy_aws/tests/test_workers.py`
- **.deregister_task_definition()** (1 connections) — `deploy_aws/tests/test_workers.py`
- **.describe_task_definition()** (1 connections) — `deploy_aws/tests/test_workers.py`
- **.list_task_definitions()** (1 connections) — `deploy_aws/tests/test_workers.py`

## Relationships

- [Worker Image Tests](Worker_Image_Tests.md) (7 shared connections)
- [AWS Worker Image Management](AWS_Worker_Image_Management.md) (5 shared connections)
- [Container Engine Adapter](Container_Engine_Adapter.md) (3 shared connections)
- [Run State Rendering](Run_State_Rendering.md) (1 shared connections)

## Source Files

- `deploy_aws/gherkai_deploy_aws/workers.py`
- `deploy_aws/tests/test_workers.py`

## Audit Trail

- EXTRACTED: 26 (84%)
- INFERRED: 5 (16%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*