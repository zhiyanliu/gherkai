#!/usr/bin/env python3
"""CDK app 入口（iac_aws_backend，ADR 0033）。

prefix 从 CDK context 读（`cdk deploy -c prefix=prod-`），默认 gherkai-——**须与 cli `--prefix` 一致**
（ADR 0033 护栏：CDK 建的名 = cli 推导名）。多环境（prod-/stage-）用不同 prefix 多次部署、各成一套资源。

account/region 从 env 取（CDK 标准 CDK_DEFAULT_ACCOUNT/REGION，由 aws CLI 凭证/配置提供）。
"""
import os

import aws_cdk as cdk

from names import DEFAULT_PREFIX
from stack import BackendStack

app = cdk.App()

# prefix：-c prefix=xxx 覆盖，默认 gherkai-。stack 名带 prefix 以支持多环境并存（prod-/stage- 各一 stack）。
prefix = app.node.try_get_context("prefix") or DEFAULT_PREFIX
stack_id = f"BackendStack-{prefix.rstrip('-') or 'default'}"

BackendStack(
    app, stack_id,
    prefix=prefix,
    env=cdk.Environment(
        account=os.environ.get("CDK_DEFAULT_ACCOUNT"),
        region=os.environ.get("CDK_DEFAULT_REGION"),
    ),
)

app.synth()
