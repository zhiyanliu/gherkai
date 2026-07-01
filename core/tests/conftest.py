"""云端 adapter 测试基建（ADR 0030 决定六）：moto 内存 mock，全程**绝不连真 AWS**。

两道保障：
1. `_fake_aws_creds`（autouse）：在**任何** boto3 client 创建前把 AWS 凭证/region 环境变量覆盖成假值——
   即便 CI 机器上有真凭证也被盖掉，且给定 region 避免 NoRegionError。这是「不烧真 AWS」的硬隔离点。
2. `mock_aws`（moto）：拦截所有 AWS 调用到内存后端，不出网。

DDB 表 schema 见 ADR 0030 决定六：PK=run_id（HASH）、SK（RANGE，值 'META'/'STATE'）。建表责任在
IaC/组合根、adapter 假定表已存在——故测试里由 fixture 建表（不由 adapter 自建）。
"""
from __future__ import annotations

import pytest

# moto 5.x：统一入口 mock_aws（旧的 mock_dynamodb/mock_s3 已废）
from moto import mock_aws

_TABLE_NAME = "yaozhou-runs"   # RunStore 表（PK=run_id, SK=META|STATE）
_BUCKET_NAME = "yaozhou-artifacts"  # ResultStore/ReportStore 对象桶


@pytest.fixture(autouse=True)
def _fake_aws_creds(monkeypatch):
    """硬隔离：设假凭证 + 固定 region，绝不误连真 AWS（moto 官方推荐套装）。autouse=每个测试都先生效。"""
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

    表 schema 按 ADR 0030 决定六：PK=run_id(S,HASH) + SK(S,RANGE)。云端 adapter 假定表/桶已存在
    （建表建桶归 IaC/测试 fixture，非 adapter）。
    """
    import boto3

    with mock_aws():
        ddb = boto3.resource("dynamodb", region_name="us-east-1")
        ddb.create_table(
            TableName=_TABLE_NAME,
            KeySchema=[
                {"AttributeName": "run_id", "KeyType": "HASH"},
                {"AttributeName": "sk", "KeyType": "RANGE"},
            ],
            AttributeDefinitions=[
                {"AttributeName": "run_id", "AttributeType": "S"},
                {"AttributeName": "sk", "AttributeType": "S"},
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
