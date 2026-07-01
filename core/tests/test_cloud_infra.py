"""步骤 0 自检（ADR 0030 决定六）：moto 测试基建可用 + 硬隔离生效。

在写任何云端 adapter 前，先证明 conftest 的 fixture 能建表/建桶、且全程不连真 AWS。
adapter 落地后各自的 round-trip 测试复用 `aws` fixture。
"""
from __future__ import annotations

import os


def test_fake_creds_hard_isolation():
    # autouse fixture 已把凭证/region 盖成假值——绝不会误用真凭证连真 AWS
    assert os.environ["AWS_ACCESS_KEY_ID"] == "testing"
    assert os.environ["AWS_SECRET_ACCESS_KEY"] == "testing"
    assert os.environ["AWS_DEFAULT_REGION"] == "us-east-1"


def test_ddb_table_and_s3_bucket_ready(aws):
    # DDB 表按 schema 建好（PK=run_id + SK），put/get 一条走内存 mock 通
    table = aws["ddb"].Table(aws["table_name"])
    table.put_item(Item={"run_id": "r1", "sk": "META", "probe": "ok"})
    got = table.get_item(Key={"run_id": "r1", "sk": "META"})["Item"]
    assert got["probe"] == "ok"

    # S3 桶建好，put/get 一个对象通
    aws["s3"].put_object(Bucket=aws["bucket"], Key="r1/probe.txt", Body=b"ok")
    body = aws["s3"].get_object(Bucket=aws["bucket"], Key="r1/probe.txt")["Body"].read()
    assert body == b"ok"


def test_ddb_native_map_single_element_update(aws):
    # 预验 ADR 决定六的关键机制：DDB 原生 Map 按 key 单元素刷（SET jobs.#sid=:js），
    # scope_id 含 / : 中文作 Map key 安全（ExpressionAttributeNames 绕开特殊字符）。
    table = aws["ddb"].Table(aws["table_name"])
    table.put_item(Item={"run_id": "r1", "sk": "STATE", "jobs": {}})
    scope_id = "features/wiki.feature:6"  # 含 / :
    table.update_item(
        Key={"run_id": "r1", "sk": "STATE"},
        UpdateExpression="SET jobs.#sid = :js",
        ExpressionAttributeNames={"#sid": scope_id},
        ExpressionAttributeValues={":js": {"status": "running", "session_id": "s1"}},
    )
    # 中文 scope_id 同样安全
    table.update_item(
        Key={"run_id": "r1", "sk": "STATE"},
        UpdateExpression="SET jobs.#sid = :js",
        ExpressionAttributeNames={"#sid": "登录场景"},
        ExpressionAttributeValues={":js": {"status": "pending"}},
    )
    jobs = table.get_item(Key={"run_id": "r1", "sk": "STATE"})["Item"]["jobs"]
    assert jobs["features/wiki.feature:6"]["status"] == "running"
    assert jobs["登录场景"]["status"] == "pending"   # 两个 scope 各刷各的、互不覆盖
