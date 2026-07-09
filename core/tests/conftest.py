"""云端 adapter 测试基建（ADR 0030 决定六）。

**两类测试、两套 fixture**（见 tests/README.md）：
- **单测（默认）**：moto 内存 mock，全程**绝不连真 AWS**。两道保障——
  1. `_fake_aws_creds`（autouse）：任何 boto3 client 创建前把 AWS 凭证/region 覆盖成假值，即便机器有真凭证也盖掉、
     且给 region 避免 NoRegionError。「不烧真 AWS」的硬隔离点。
  2. `mock_aws`（moto）：拦截所有 AWS 调用到内存后端，不出网。
- **集成测试（`@pytest.mark.integration`，默认 deselect）**：连**真** DDB/S3，专测 moto 抓不到的真语义。
  `_fake_aws_creds` 对它**让路**（不覆盖真凭证）；`real_aws` fixture 读 `AWS_DDB_TABLE`/`AWS_S3_BUCKET` 环境变量拿真表/桶名，
  没设就 skip（不误连、不报错）。用真凭证（default profile）。见 `real_aws` fixture 与 tests/README.md。

DDB 表 schema 见 ADR 0030 决定六：分区键 run_id（HASH）、排序键 item_type（RANGE，值 'META'/'STATE'）。建表责任在
IaC/组合根、adapter 假定表已存在——单测由 fixture 建（moto 内存表），集成测试假定真表/桶已由你预建（见 README）。
"""
from __future__ import annotations

import os

import pytest

# moto 5.x：统一入口 mock_aws（旧的 mock_dynamodb/mock_s3 已废）
from moto import mock_aws

_TABLE_NAME = "gherkai-runs"   # RunStore 表（分区键 run_id + 排序键 item_type=META|STATE）
_BUCKET_NAME = "gherkai-artifacts"  # ResultStore/ReportStore 对象桶

# 集成测试读的环境变量名（真表/真桶名由你建好后经它们传入；没设 → 集成测试 skip）
_IT_TABLE_ENV = "AWS_DDB_TABLE"
_IT_BUCKET_ENV = "AWS_S3_BUCKET"


@pytest.fixture(autouse=True)
def _fake_aws_creds(request, monkeypatch):
    """硬隔离：设假凭证 + 固定 region，绝不误连真 AWS（moto 官方推荐套装）。autouse=每个测试都先生效。

    **对 `@pytest.mark.integration` 让路**：集成测试要连真 AWS，若给它盖假凭证会连不上——故检测到
    integration 标记就直接返回、不覆盖凭证（让真 default profile 生效）。单测无此标记，照旧硬隔离。
    """
    if request.node.get_closest_marker("integration") is not None:
        return  # 集成测试：不盖凭证，用真 default profile
    monkeypatch.setenv("AWS_ACCESS_KEY_ID", "testing")
    monkeypatch.setenv("AWS_SECRET_ACCESS_KEY", "testing")
    monkeypatch.setenv("AWS_SECURITY_TOKEN", "testing")
    monkeypatch.setenv("AWS_SESSION_TOKEN", "testing")
    monkeypatch.setenv("AWS_DEFAULT_REGION", "us-east-1")
    # 防御：即便某处误配了真 endpoint，也清掉
    monkeypatch.delenv("AWS_ENDPOINT_URL", raising=False)


@pytest.fixture
def aws(_fake_aws_creds):
    """在 moto mock 下建好 DDB 表 + S3 桶，产出 (boto3 resource/client, 名字) 供云端 adapter 测试注入。

    表 schema 按 ADR 0030 决定六：分区键 run_id(S,HASH) + 排序键 item_type(S,RANGE)。云端 adapter 假定表/桶
    已存在（建表建桶归 IaC/测试 fixture，非 adapter）。
    """
    import boto3

    with mock_aws():
        ddb = boto3.resource("dynamodb", region_name="us-east-1")
        ddb.create_table(
            TableName=_TABLE_NAME,
            KeySchema=[
                {"AttributeName": "run_id", "KeyType": "HASH"},
                {"AttributeName": "item_type", "KeyType": "RANGE"},
            ],
            AttributeDefinitions=[
                {"AttributeName": "run_id", "AttributeType": "S"},
                {"AttributeName": "item_type", "AttributeType": "S"},
            ],
            BillingMode="PAY_PER_REQUEST",
        )
        s3 = boto3.client("s3", region_name="us-east-1")
        s3.create_bucket(Bucket=_BUCKET_NAME)

        yield {
            "ddb": ddb,
            "table_name": _TABLE_NAME,
            "s3": s3,
            "bucket": _BUCKET_NAME,
        }


@pytest.fixture
def ddb_run_store(aws):
    """配好的 DynamoDBRunStore（注入 aws fixture 建好的表），供 RunStore 对拍测试。"""
    from core.adapters.run_store.ddb import DynamoDBRunStore

    return DynamoDBRunStore(aws["ddb"].Table(aws["table_name"]))


@pytest.fixture
def s3_result_store(aws):
    """配好的 S3ResultStore（注入 aws fixture 建好的桶），供 ResultStore 对拍测试。"""
    from core.adapters.result_store.s3 import S3ResultStore

    return S3ResultStore(aws["s3"], aws["bucket"])


@pytest.fixture
def s3_report_store(aws):
    """配好的 S3ReportStore（注入 aws fixture 建好的桶），供 ReportStore 对拍测试。"""
    from core.adapters.report_store.s3 import S3ReportStore

    return S3ReportStore(aws["s3"], aws["bucket"])


@pytest.fixture
def arg_offloader(aws):
    """配好的 S3StepArgumentOffloader（注入 aws fixture 建好的桶），供 StepArgument offload 测试。"""
    from core.adapters.run_store.arg_offload import S3StepArgumentOffloader

    return S3StepArgumentOffloader(aws["s3"], aws["bucket"])


@pytest.fixture
def ddb_run_store_offload(aws, arg_offloader):
    """挂了 S3 offload 的 DynamoDBRunStore：RunMeta 的 docString/dataTable 搬 S3、META 只留指针。"""
    from core.adapters.run_store.ddb import DynamoDBRunStore

    return DynamoDBRunStore(aws["ddb"].Table(aws["table_name"]), arg_offloader=arg_offloader)


# events 表（ADR 0024「DynamoDB 作 events-out」）：PK=run_id#scope_id、SK=seq（Number）。FargateEngine 测试用。
_EVENTS_TABLE_NAME = "gherkai-events"


@pytest.fixture
def fargate(_fake_aws_creds):
    """moto mock 下建全 FargateEngine 依赖：EC2 网络 + ECS FARGATE cluster/task-def + events 表 + S3 桶。

    **moto 5.2.2 ECS Fargate 坑规避（实测逼近所得，纯 setup、无 monkeypatch）**：
    - VPC 必开 `EnableDnsHostnames`，否则 run_task 建 ENI 时 `AttributeError: private_dns_name`；
    - task-def 顶层 + 每 container 都给整数 cpu/memory，否则 `TypeError: int += NoneType`；
    - awsvpcConfiguration 必显式给 securityGroups，否则 `KeyError`；
    - **pin `ecs::task` transition**，否则每次 `describe_tasks` 都把 lastStatus 推进一格（RUNNING→…→STOPPED），
      测试非确定。teardown `unset_transition` 还原（该配置全局、不随 mock_aws 退出复位，须手动还原防污染后续测试）。

    **moto ECS 状态机失真（绿≠对，务必知）**：container `exitCode` 恒 0、`lastStatus` 恒 PENDING、task.lastStatus
    由 describe 次数驱动——**退出码/容器终止语义 moto 测不了**，FargateEngine 的退出码解析（`_task_exit_code`/
    `_raise_for_exit`）用**构造 describe 响应 dict** 的纯单测锁逻辑，真实时序 defer 真跑（WP3-B）。moto 只忠实测
    run_task/stop_task 编排 + DDB Query 迭代器。
    """
    import boto3
    from moto.moto_api import state_manager

    region = "us-east-1"
    with mock_aws():
        state_manager.set_transition("ecs::task", {"progression": "manual", "times": 10**9})
        try:
            ec2 = boto3.client("ec2", region_name=region)
            ecs = boto3.client("ecs", region_name=region)
            ddb = boto3.resource("dynamodb", region_name=region)
            s3 = boto3.client("s3", region_name=region)

            vpc = ec2.create_vpc(CidrBlock="10.0.0.0/16")["Vpc"]["VpcId"]
            ec2.modify_vpc_attribute(VpcId=vpc, EnableDnsHostnames={"Value": True})
            ec2.modify_vpc_attribute(VpcId=vpc, EnableDnsSupport={"Value": True})
            subnet = ec2.create_subnet(
                VpcId=vpc, CidrBlock="10.0.1.0/24", AvailabilityZone=f"{region}a")["Subnet"]["SubnetId"]
            sg = ec2.create_security_group(
                GroupName="fargate-sg", Description="fargate sg", VpcId=vpc)["GroupId"]
            cluster = ecs.create_cluster(clusterName="test-cluster")["cluster"]["clusterArn"]
            task_def = ecs.register_task_definition(
                family="test-task",
                requiresCompatibilities=["FARGATE"],
                networkMode="awsvpc",
                cpu="256", memory="512",
                containerDefinitions=[{
                    "name": "worker", "image": "busybox:latest",
                    "cpu": 256, "memory": 512, "essential": True,
                }],
            )["taskDefinition"]["taskDefinitionArn"]

            # events 表：PK=pk(run_id#scope_id, S) + SK=seq(N)
            ddb.create_table(
                TableName=_EVENTS_TABLE_NAME,
                KeySchema=[
                    {"AttributeName": "pk", "KeyType": "HASH"},
                    {"AttributeName": "seq", "KeyType": "RANGE"},
                ],
                AttributeDefinitions=[
                    {"AttributeName": "pk", "AttributeType": "S"},
                    {"AttributeName": "seq", "AttributeType": "N"},
                ],
                BillingMode="PAY_PER_REQUEST",
            )
            s3.create_bucket(Bucket=_BUCKET_NAME)

            yield {
                "ec2": ec2, "ecs": ecs, "ddb": ddb, "s3": s3,
                "cluster": cluster, "task_def": task_def,
                "subnet": subnet, "sg": sg,
                "events_table": ddb.Table(_EVENTS_TABLE_NAME),
                "events_table_name": _EVENTS_TABLE_NAME,
                "bucket": _BUCKET_NAME,
                "container_name": "worker",
                "network_config": {
                    "subnets": [subnet], "securityGroups": [sg], "assignPublicIp": "ENABLED",
                },
            }
        finally:
            state_manager.unset_transition("ecs::task")  # 还原全局，防污染后续测试


# ============================================================================
# 集成测试 fixture（连真 DDB/S3，@pytest.mark.integration；默认 deselect，见 pyproject addopts）
# ============================================================================


@pytest.fixture
def real_aws():
    """连真 DDB/S3 的句柄（真表/桶名读环境变量），供集成测试。**没设环境变量就 skip**（不误连、不报错）。

    需你先建好真表 + 真桶（见 tests/README.md），把名字经 `AWS_DDB_TABLE`/`AWS_S3_BUCKET`
    传入。用真凭证（default profile，`_fake_aws_creds` 对 integration 标记让路）。region 取 AWS_REGION/
    AWS_DEFAULT_REGION，默认 us-east-1。

    产出 dict：{ddb, table_name, s3, bucket}——与单测 `aws` fixture 同形，故集成用例可复用单测的构造逻辑。
    **自清理**：yield 后删本次用例经 adapter 写进真表/真桶的所有条目（按 run_id / key 前缀），不留垃圾。
    整批清理 key 由用例登记进返回 dict 的 `_cleanup_run_ids` / `_cleanup_prefixes`（helper 见下）。
    """
    table_name = os.environ.get(_IT_TABLE_ENV)
    bucket = os.environ.get(_IT_BUCKET_ENV)
    if not table_name or not bucket:
        pytest.skip(
            f"集成测试需设 {_IT_TABLE_ENV} + {_IT_BUCKET_ENV}（真 DDB 表 + S3 桶名）——见 tests/README.md。未设，跳过。"
        )

    import boto3

    region = os.environ.get("AWS_REGION") or os.environ.get("AWS_DEFAULT_REGION") or "us-east-1"
    ddb = boto3.resource("dynamodb", region_name=region)
    s3 = boto3.client("s3", region_name=region)

    run_ids: list[str] = []   # 用例登记：清理时按 run_id 删 DDB 两 item（META/STATE）
    prefixes: list[str] = []  # 用例登记：清理时按 key 前缀清 S3 对象

    ctx = {
        "ddb": ddb,
        "table_name": table_name,
        "s3": s3,
        "bucket": bucket,
        "cleanup_run_id": run_ids.append,     # 用例调它登记要清的 run_id
        "cleanup_prefix": prefixes.append,    # 用例调它登记要清的 S3 前缀
    }
    try:
        yield ctx
    finally:
        # 自清理：删本次用例写进真表/真桶的数据（尽力而为，逐个吞异常不影响其它清理）
        table = ddb.Table(table_name)
        for rid in run_ids:
            for item_type in ("META", "STATE"):
                try:
                    table.delete_item(Key={"run_id": rid, "item_type": item_type})
                except Exception:  # noqa: BLE001  清理尽力而为
                    pass
        for prefix in prefixes:
            try:
                resp = s3.list_objects_v2(Bucket=bucket, Prefix=prefix)
                objs = [{"Key": o["Key"]} for o in resp.get("Contents", [])]
                if objs:
                    s3.delete_objects(Bucket=bucket, Delete={"Objects": objs})
            except Exception:  # noqa: BLE001  清理尽力而为
                pass
