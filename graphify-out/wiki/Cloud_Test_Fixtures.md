# Cloud Test Fixtures

> 21 nodes · cohesion 0.13

## Key Concepts

- **conftest.py** (14 connections) — `core/tests/conftest.py`
- **fixture** (9 connections)
- **arg_offloader()** (4 connections) — `core/tests/conftest.py`
- **ddb_run_store()** (4 connections) — `core/tests/conftest.py`
- **ddb_run_store_offload()** (4 connections) — `core/tests/conftest.py`
- **s3_report_store()** (4 connections) — `core/tests/conftest.py`
- **s3_result_store()** (4 connections) — `core/tests/conftest.py`
- **aws()** (3 connections) — `core/tests/conftest.py`
- **_fake_aws_creds()** (3 connections) — `core/tests/conftest.py`
- **fargate()** (3 connections) — `core/tests/conftest.py`
- **real_aws()** (3 connections) — `core/tests/conftest.py`
- **云端 adapter 测试基建（ADR 0030 决定六）。 **两类测试、两套 fixture**（见 tests/README.md）： -…** (1 connections) — `core/tests/conftest.py`
- **配好的 S3ReportStore（注入 aws fixture 建好的桶），供 ReportStore 对拍测试。** (1 connections) — `core/tests/conftest.py`
- **配好的 S3StepArgumentOffloader（注入 aws fixture 建好的桶），供 StepArgument offload 测试。** (1 connections) — `core/tests/conftest.py`
- **挂了 S3 offload 的 DynamoDBRunStore：RunMeta 的 docString/dataTable 搬 S3、META 只留指针。** (1 connections) — `core/tests/conftest.py`
- **moto mock 下建全 FargateEngine 依赖：EC2 网络 + ECS FARGATE cluster/task-def + events 表…** (1 connections) — `core/tests/conftest.py`
- **连真 DDB/S3 的句柄（真表/桶名读环境变量），供集成测试。**没设环境变量就 skip**（不误连、不报错）。 需你先建好真表 + 真桶（见…** (1 connections) — `core/tests/conftest.py`
- **硬隔离：设假凭证 + 固定 region，绝不误连真 AWS（moto 官方推荐套装）。autouse=每个测试都先生效。 **对…** (1 connections) — `core/tests/conftest.py`
- **在 moto mock 下建好 DDB 表 + S3 桶，产出 (boto3 resource/client, 名字) 供云端 adapter 测试注入。 表…** (1 connections) — `core/tests/conftest.py`
- **配好的 DynamoDBRunStore（注入 aws fixture 建好的表），供 RunStore 对拍测试。** (1 connections) — `core/tests/conftest.py`
- **配好的 S3ResultStore（注入 aws fixture 建好的桶），供 ResultStore 对拍测试。** (1 connections) — `core/tests/conftest.py`

## Relationships

- [Boto Guard & S3 Offload](Boto_Guard_%26_S3_Offload.md) (3 shared connections)
- [S3 Report Store & Subprocess](S3_Report_Store_%26_Subprocess.md) (2 shared connections)
- [S3 Argument Offloader](S3_Argument_Offloader.md) (2 shared connections)
- [S3 Result Store](S3_Result_Store.md) (2 shared connections)

## Source Files

- `core/tests/conftest.py`

## Audit Trail

- EXTRACTED: 37 (100%)
- INFERRED: 0 (0%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*