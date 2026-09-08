"""synth 夹具（非测试模块，同 `core/tests/fake_engine.py` 的惯例）：造 `BackendStack` / 模板。

单独成模块是因为**两个**测试文件要用同一份构造（stack 断言 + Lambda asset 内容）——各写一份就会在
「version context 必给」这类前置上漂移。
"""
from __future__ import annotations

import aws_cdk as cdk
from aws_cdk.assertions import Template

from gherkai_deploy_aws.cli import CDK_FEATURE_FLAGS
from gherkai_deploy_aws.stack import BackendStack

# 版本戳 context 必给（无隐式默认，见 BackendStack._resolve_version）——测试统一用这个假版本。
STAMP_VERSION = "1.4.0"

# synth 用的假环境。账号 000…0 是**有意的**：IAM 护栏要拿它反证「系统 browser ARN 的 account 段不是客户账户」
# （见 test_stack.py::test_task_role_resource_arns_narrowed 的 copy-account 陷阱注释）。
ACCOUNT = "000000000000"
REGION = "us-east-1"


def make_stack(prefix: str = "gherkai-", context: dict | None = None) -> BackendStack:
    """**带上命令真会给的 CDK 特性开关**（`cli.CDK_FEATURE_FLAGS`）——特性开关会改变合成出的资源形态，
    测试用默认开关就等于在断言一份没人部署的模板。真源在 provider 一处，这里只引用。"""
    app = cdk.App(context={**CDK_FEATURE_FLAGS, "version": STAMP_VERSION, **(context or {})})
    return BackendStack(app, "T", prefix=prefix, env=cdk.Environment(account=ACCOUNT, region=REGION))


def make_template(prefix: str = "gherkai-", context: dict | None = None) -> Template:
    return Template.from_stack(make_stack(prefix, context))
