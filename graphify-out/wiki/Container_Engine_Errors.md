# Container Engine Errors

> 15 nodes · cohesion 0.13

## Key Concepts

- **ContainerError** (22 connections) — `deploy_aws/gherkai_deploy_aws/container.py`
- **CountingEcs** (9 connections) — `deploy_aws/tests/test_workers.py`
- **Spy** (9 connections) — `deploy_aws/tests/test_workers.py`
- **CleanupOutcome** (6 connections) — `deploy_aws/gherkai_deploy_aws/workers.py`
- **.pull()** (2 connections) — `deploy_aws/tests/test_workers.py`
- **Exception** (1 connections)
- **容器引擎侧的失败（**用户可修**：引擎没装、daemon 没起、镜像不存在、push 被拒……）。 `str(exc)`…** (1 connections) — `deploy_aws/gherkai_deploy_aws/container.py`
- **一次 pass 的结果：删掉的 revision + 留到下次的（ARN、原因）。**生产调用点（push-worker / deploy 末步） 只看…** (1 connections) — `deploy_aws/gherkai_deploy_aws/workers.py`
- **.describe_task_definition()** (1 connections) — `deploy_aws/tests/test_workers.py`
- **.__getattr__()** (1 connections) — `deploy_aws/tests/test_workers.py`
- **.__init__()** (1 connections) — `deploy_aws/tests/test_workers.py`
- **boto3 client 的记名壳（验「这一步之前一次 AWS 都没调」）。** (1 connections) — `deploy_aws/tests/test_workers.py`
- **ECS client 的记参壳（数「同一个 task-def 被 describe 了几次」）——`Spy` 只记方法名，数不出这个。** (1 connections) — `deploy_aws/tests/test_workers.py`
- **.__getattr__()** (1 connections) — `deploy_aws/tests/test_workers.py`
- **.__init__()** (1 connections) — `deploy_aws/tests/test_workers.py`

## Relationships

- [Worker Image Management Tests](Worker_Image_Management_Tests.md) (11 shared connections)
- [Container Engine Wrapper](Container_Engine_Wrapper.md) (9 shared connections)
- [Worker Image Lifecycle](Worker_Image_Lifecycle.md) (7 shared connections)
- [Task Definition Lineage Cleanup](Task_Definition_Lineage_Cleanup.md) (1 shared connections)
- [Task Definition Cleanup](Task_Definition_Cleanup.md) (1 shared connections)
- [Run Result Aggregation Tree](Run_Result_Aggregation_Tree.md) (1 shared connections)

## Source Files

- `deploy_aws/gherkai_deploy_aws/container.py`
- `deploy_aws/gherkai_deploy_aws/workers.py`
- `deploy_aws/tests/test_workers.py`

## Audit Trail

- EXTRACTED: 30 (68%)
- INFERRED: 14 (32%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*