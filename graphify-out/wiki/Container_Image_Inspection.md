# Container Image Inspection

> 27 nodes · cohesion 0.08

## Key Concepts

- **ContainerError** (22 connections) — `deploy_aws/gherkai_deploy_aws/container.py`
- **ImageInfo** (15 connections) — `deploy_aws/gherkai_deploy_aws/container.py`
- **test_rederive_enumerates_ssm_once_and_reads_the_template_once_per_engine()** (10 connections) — `deploy_aws/tests/test_workers.py`
- **CountingEcs** (9 connections) — `deploy_aws/tests/test_workers.py`
- **Spy** (9 connections) — `deploy_aws/tests/test_workers.py`
- **test_rederive_does_not_read_the_template_when_nothing_is_stale()** (9 connections) — `deploy_aws/tests/test_workers.py`
- **.inspect()** (5 connections) — `deploy_aws/gherkai_deploy_aws/container.py`
- **.matches_target_platform()** (2 connections) — `deploy_aws/gherkai_deploy_aws/container.py`
- **.platform()** (2 connections) — `deploy_aws/gherkai_deploy_aws/container.py`
- **test_target_platform_judgement()** (2 connections) — `deploy_aws/tests/test_container.py`
- **.inspect()** (2 connections) — `deploy_aws/tests/test_workers.py`
- **.pull()** (2 connections) — `deploy_aws/tests/test_workers.py`
- **Exception** (1 connections)
- **本地镜像的存在 + 平台 + registry digest 列表。镜像不存在 → `ImageInfo(exists=False)`（**不抛**：…** (1 connections) — `deploy_aws/gherkai_deploy_aws/container.py`
- **容器引擎侧的失败（**用户可修**：引擎没装、daemon 没起、镜像不存在、push 被拒……）。 `str(exc)`…** (1 connections) — `deploy_aws/gherkai_deploy_aws/container.py`
- **`inspect` 的结果——**只有三件事**：在不在、什么平台、有哪些 registry digest。 `repo_digests` 是…** (1 connections) — `deploy_aws/gherkai_deploy_aws/container.py`
- **`linux/amd64` 形态的人读串（未知段落写 `?`，用于报错文案）。** (1 connections) — `deploy_aws/gherkai_deploy_aws/container.py`
- **是否 linux/amd64（ADR 0038 固定架构）。** (1 connections) — `deploy_aws/gherkai_deploy_aws/container.py`
- **.describe_task_definition()** (1 connections) — `deploy_aws/tests/test_workers.py`
- **.__getattr__()** (1 connections) — `deploy_aws/tests/test_workers.py`
- **.__init__()** (1 connections) — `deploy_aws/tests/test_workers.py`
- **boto3 client 的记名壳（验「这一步之前一次 AWS 都没调」）。** (1 connections) — `deploy_aws/tests/test_workers.py`
- **ECS client 的记参壳（数「同一个 task-def 被 describe 了几次」）——`Spy` 只记方法名，数不出这个。** (1 connections) — `deploy_aws/tests/test_workers.py`
- **重派生是「枚举一次、逐引擎筛」+「repo URI 每引擎算一次」：SSM 全量枚举次数不随引擎数增长、 模板 describe 次数不随 variant…** (1 connections) — `deploy_aws/tests/test_workers.py`
- **模板没变（deploy 重新运行的常态）→ 一次模板 describe 都不打：判定只用映射里记的模板 ARN。** (1 connections) — `deploy_aws/tests/test_workers.py`
- *... and 2 more nodes in this community*

## Relationships

- [Container Worker Image Tests](Container_Worker_Image_Tests.md) (17 shared connections)
- [Container Engine Port](Container_Engine_Port.md) (13 shared connections)
- [AWS Worker Image Registry](AWS_Worker_Image_Registry.md) (9 shared connections)
- [Task Definition Revision Cleanup](Task_Definition_Revision_Cleanup.md) (3 shared connections)
- [List Workers Command](List_Workers_Command.md) (3 shared connections)
- [Revision Cleanup Pass](Revision_Cleanup_Pass.md) (1 shared connections)

## Source Files

- `deploy_aws/gherkai_deploy_aws/container.py`
- `deploy_aws/tests/test_container.py`
- `deploy_aws/tests/test_workers.py`

## Audit Trail

- EXTRACTED: 59 (79%)
- INFERRED: 16 (21%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*