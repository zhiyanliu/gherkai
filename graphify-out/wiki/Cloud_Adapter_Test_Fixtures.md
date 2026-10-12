# Cloud Adapter Test Fixtures

> 18 nodes · cohesion 0.11

## Key Concepts

- **core/tests/conftest.py** (14 connections) — `core/tests/conftest.py`
- **real_aws()** (5 connections) — `core/tests/conftest.py`
- **arg_offloader()** (4 connections) — `core/tests/conftest.py`
- **ddb_run_store()** (4 connections) — `core/tests/conftest.py`
- **ddb_run_store_offload()** (4 connections) — `core/tests/conftest.py`
- **_fake_aws_creds()** (4 connections) — `core/tests/conftest.py`
- **s3_report_store()** (4 connections) — `core/tests/conftest.py`
- **s3_result_store()** (4 connections) — `core/tests/conftest.py`
- **fargate()** (3 connections) — `core/tests/conftest.py`
- **云端 adapter 测试基建（ADR 0030 决定六）。 **两类测试、两套 fixture**（见 tests/README.md）： -…** (1 connections) — `core/tests/conftest.py`
- **配好的 S3ReportStore（注入 aws fixture 建好的桶），供 ReportStore 对拍测试。** (1 connections) — `core/tests/conftest.py`
- **配好的 S3StepArgumentOffloader（注入 aws fixture 建好的桶），供 StepArgument offload 测试。** (1 connections) — `core/tests/conftest.py`
- **挂了 S3 offload 的 DynamoDBRunStore：RunMeta 的 docString/dataTable 搬 S3、META 只留指针。** (1 connections) — `core/tests/conftest.py`
- **moto mock 下建全 FargateEngine 依赖：EC2 网络 + ECS FARGATE cluster/task-def + events 表…** (1 connections) — `core/tests/conftest.py`
- **连真 DDB/S3 的句柄（真表/桶名读环境变量），供集成测试。**没设环境变量就 skip**（不误连、不报错）。 需你先建好真表 + 真桶（见…** (1 connections) — `core/tests/conftest.py`
- **硬隔离：设假凭证 + 固定 region，绝不误连真 AWS（moto 官方推荐套装）。autouse 表示每个测试都先生效。 **对…** (1 connections) — `core/tests/conftest.py`
- **配好的 DynamoDBRunStore（注入 aws fixture 建好的表），供 RunStore 对拍测试。** (1 connections) — `core/tests/conftest.py`
- **配好的 S3ResultStore（注入 aws fixture 建好的桶），供 ResultStore 对拍测试。** (1 connections) — `core/tests/conftest.py`

## Relationships

- [Test Fixtures And Env](Test_Fixtures_And_Env.md) (8 shared connections)
- [Job Explain Data Model](Job_Explain_Data_Model.md) (4 shared connections)
- [S3 Report Store](S3_Report_Store.md) (2 shared connections)
- [Step Argument S3 Offload](Step_Argument_S3_Offload.md) (2 shared connections)
- [S3 Result Store](S3_Result_Store.md) (2 shared connections)
- [Contributor Docs And ADRs](Contributor_Docs_And_ADRs.md) (2 shared connections)
- [Moto DynamoDB/S3 Fixtures](Moto_DynamoDB-S3_Fixtures.md) (1 shared connections)

## Source Files

- `core/tests/conftest.py`

## Audit Trail

- EXTRACTED: 38 (100%)
- INFERRED: 0 (0%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*