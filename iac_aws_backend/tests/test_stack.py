"""BackendStack 合成断言测试（ADR 0033）：纯本地 synth、不碰 AWS。

用 CDK assertions.Template 断言关键契约——尤其**与 cli 侧命名/schema 的单一事实源对齐点**（ADR 0033 护栏）：
表/桶/task-def 名、events TTL 属性、container 名不带 prefix、SSM 路径。防未来改 stack 时漂移。
跑：uv run pytest。
"""
from __future__ import annotations

import json

import aws_cdk as cdk
from aws_cdk.assertions import Template, Match

from stack import BackendStack


def _template(prefix: str = "gherkai-") -> Template:
    app = cdk.App()
    stack = BackendStack(app, "T", prefix=prefix,
                         env=cdk.Environment(account="000000000000", region="us-east-1"))
    return Template.from_stack(stack)


def test_two_dynamodb_tables_with_correct_schema():
    t = _template()
    t.resource_count_is("AWS::DynamoDB::Table", 2)
    # runs 表：PK=run_id / SK=item_type
    t.has_resource_properties("AWS::DynamoDB::Table", {
        "TableName": "gherkai-runs",
        "KeySchema": [
            {"AttributeName": "run_id", "KeyType": "HASH"},
            {"AttributeName": "item_type", "KeyType": "RANGE"},
        ],
    })
    # events 表：PK=pk / SK=seq + TTL expires_at（ADR 0033/0024）
    t.has_resource_properties("AWS::DynamoDB::Table", {
        "TableName": "gherkai-events",
        "KeySchema": [
            {"AttributeName": "pk", "KeyType": "HASH"},
            {"AttributeName": "seq", "KeyType": "RANGE"},
        ],
        "TimeToLiveSpecification": {"AttributeName": "expires_at", "Enabled": True},
    })


def test_events_table_seq_is_number_type():
    # seq 必须 Number（N）——core FargateEngine Query gt(int) 依赖数值比较、保序（非字符串序）
    t = _template()
    t.has_resource_properties("AWS::DynamoDB::Table", {
        "TableName": "gherkai-events",
        "AttributeDefinitions": Match.array_with([
            {"AttributeName": "seq", "AttributeType": "N"},
        ]),
    })


def test_artifacts_bucket_private():
    t = _template()
    t.resource_count_is("AWS::S3::Bucket", 1)
    t.has_resource_properties("AWS::S3::Bucket", {
        "BucketName": "gherkai-artifacts",
        "PublicAccessBlockConfiguration": {
            "BlockPublicAcls": True, "BlockPublicPolicy": True,
            "IgnorePublicAcls": True, "RestrictPublicBuckets": True,
        },
    })


def test_two_task_defs_container_name_without_prefix():
    # **container 名 = {engine}-worker（不带 prefix）**——cli RunTask containerOverrides[].name 逐字匹配（ADR 0033 硬契约）。
    t = _template()
    t.resource_count_is("AWS::ECS::TaskDefinition", 2)
    for engine in ("novaact", "midscene"):
        t.has_resource_properties("AWS::ECS::TaskDefinition", {
            "Family": f"gherkai-{engine}-worker",                       # family 带 prefix
            "ContainerDefinitions": Match.array_with([
                Match.object_like({"Name": f"{engine}-worker"}),        # container 名不带 prefix
            ]),
        })


def test_two_ecr_repos():
    t = _template()
    t.resource_count_is("AWS::ECR::Repository", 2)
    for engine in ("novaact", "midscene"):
        t.has_resource_properties("AWS::ECR::Repository", {"RepositoryName": f"gherkai-{engine}-worker"})


def test_ssm_params_with_prefix_path():
    t = _template()
    t.has_resource_properties("AWS::SSM::Parameter", {
        "Name": "/gherkai-backend/subnets", "Type": "StringList",
    })
    t.has_resource_properties("AWS::SSM::Parameter", {
        "Name": "/gherkai-backend/security-groups", "Type": "StringList",
    })


def test_task_role_has_events_putitem_not_runs():
    # task role 最小权限：events 表 PutItem，**不给 runs 表**（worker 绝不碰 RunState，ADR 0024/0030 单写者）。
    t = _template()
    # events 表 PutItem 出现在某个 policy（两个引擎 task role 都有）
    t.has_resource_properties("AWS::IAM::Policy", {
        "PolicyDocument": {
            "Statement": Match.array_with([
                Match.object_like({
                    "Action": "dynamodb:PutItem",
                    "Resource": Match.string_like_regexp(r".*gherkai-events.*"),
                }),
            ]),
        },
    })
    # **负向护栏（契约的关键一半）**：没有任何 policy statement 的 Resource 指向 runs 表——worker 绝不碰 RunState
    # （单写者，ADR 0024/0030）。遍历所有 IAM policy 的所有 statement，断言无一 Resource 命中 gherkai-runs。
    # （光验 events PutItem「存在」是假护栏：误加 runs 表写权限时子集匹配仍绿——见 dim-iac-01 review。）
    for policy in t.find_resources("AWS::IAM::Policy").values():
        for stmt in policy["Properties"]["PolicyDocument"]["Statement"]:
            res = json.dumps(stmt.get("Resource", ""))  # Resource 可能是 str / dict(Fn::Join) / list，统一序列化后搜
            assert "gherkai-runs" not in res, f"task role 不应含指向 runs 表的权限：{stmt}"


def test_prefix_switches_whole_set():
    # 两层命名核心：-c prefix=prod- 切整套名，container 名仍不带 prefix。
    t = _template(prefix="prod-")
    t.has_resource_properties("AWS::DynamoDB::Table", {"TableName": "prod-runs"})
    t.has_resource_properties("AWS::DynamoDB::Table", {"TableName": "prod-events"})
    t.has_resource_properties("AWS::S3::Bucket", {"BucketName": "prod-artifacts"})
    t.has_resource_properties("AWS::ECS::TaskDefinition", {
        "Family": "prod-novaact-worker",
        "ContainerDefinitions": Match.array_with([Match.object_like({"Name": "novaact-worker"})]),  # 仍不带 prefix
    })
    t.has_resource_properties("AWS::SSM::Parameter", {"Name": "/prod-backend/subnets"})


def test_execution_role_and_two_task_roles():
    # 3 role：1 execution role（共享）+ 2 task role（每引擎分立，最小权限，ADR 0033）。
    t = _template()
    t.resource_count_is("AWS::IAM::Role", 3)
