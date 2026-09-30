# AWS Call Counting Spies

> 11 nodes · cohesion 0.18

## Key Concepts

- **test_rederive_enumerates_ssm_once_and_reads_the_template_once_per_engine()** (10 connections) — `deploy_aws/tests/test_workers.py`
- **CountingEcs** (7 connections) — `deploy_aws/tests/test_workers.py`
- **Spy** (7 connections) — `deploy_aws/tests/test_workers.py`
- **.describe_task_definition()** (1 connections) — `deploy_aws/tests/test_workers.py`
- **.__getattr__()** (1 connections) — `deploy_aws/tests/test_workers.py`
- **.__init__()** (1 connections) — `deploy_aws/tests/test_workers.py`
- **boto3 client 的记名壳（验「这一步之前一次 AWS 都没调」）。** (1 connections) — `deploy_aws/tests/test_workers.py`
- **ECS client 的记参壳（数「同一个 task-def 被 describe 了几次」）——`Spy` 只记方法名，数不出这个。** (1 connections) — `deploy_aws/tests/test_workers.py`
- **重派生是「枚举一次、逐引擎筛」+「repo URI 每引擎算一次」：SSM 全量枚举次数不随引擎数增长、 模板 describe 次数不随 variant…** (1 connections) — `deploy_aws/tests/test_workers.py`
- **.__getattr__()** (1 connections) — `deploy_aws/tests/test_workers.py`
- **.__init__()** (1 connections) — `deploy_aws/tests/test_workers.py`

## Relationships

- [Worker Push Deploy Tests](Worker_Push_Deploy_Tests.md) (10 shared connections)
- [Worker Image Management](Worker_Image_Management.md) (2 shared connections)

## Source Files

- `deploy_aws/tests/test_workers.py`

## Audit Trail

- EXTRACTED: 22 (100%)
- INFERRED: 0 (0%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*