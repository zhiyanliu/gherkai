"""CDK app 入口（`gherkai_deploy_aws`，ADR 0033 资源装配 / ADR 0037 决策 6 部署形态）。

**不是给人直接敲的入口**：`gherkai deploy` 在临时工作目录生成 `cdk.json`，其 `app` 指向本模块
（`<sys.executable> -m gherkai_deploy_aws.app`，见 `cli.Provider`），由 cdk CLI 起本进程合成模板。
「clone repo + 裸 cdk deploy」不再是正式部署形态（相对路径拼 asset、vpc context 坑外露，ADR 0037 决策 6）——
contributor 想手工合成也走 `gherkai deploy --synth-only DIR`，别裸跑本模块。

context 旋钮全由命令拼给（ADR 0037 决策 6「flag 面对齐 stack 与 app 的全部 context 旋钮」）：
`prefix`（默认 `gherkai-`，**须与 cli `--prefix` 一致**，ADR 0033 护栏：CDK 建的名 = cli 推导名）、
`vpc_id` / `use_default_vpc`（VPC 三档，见 `stack._network`）、`stop_timeout`（grace 标定，ADR 0032）、
`version`（**必给**、无隐式默认，见 `stack._resolve_version`——裸跑缺它即 fail-fast，这是有意的）。
多环境（prod-/stage-）= 不同 prefix 各部署一套，stack 名随 prefix（`names.stack_name`）。

account/region 从 env 取（CDK 标准 `CDK_DEFAULT_ACCOUNT`/`CDK_DEFAULT_REGION`——cdk CLI 起 app 时按解析到的
凭证/profile 注入；裸跑无 cdk CLI 时二者缺失 → env-agnostic stack，`from_lookup` 会自行报错）。
"""
from __future__ import annotations

import os

import aws_cdk as cdk

from gherkai_deploy_aws import names
from gherkai_deploy_aws.stack import BackendStack


def main() -> None:
    app = cdk.App()
    # prefix：-c prefix=xxx 覆盖，默认 gherkai-。stack 名带 prefix 以支持多环境并存（prod-/stage- 各一 stack）——
    # 推导走 names.stack_name 单一真源（cli 的 VPC 档三态比对 DescribeStacks 用同一个名）。
    prefix = app.node.try_get_context("prefix") or names.DEFAULT_PREFIX
    BackendStack(
        app, names.stack_name(prefix),
        prefix=prefix,
        env=cdk.Environment(
            account=os.environ.get("CDK_DEFAULT_ACCOUNT"),
            region=os.environ.get("CDK_DEFAULT_REGION"),
        ),
    )
    app.synth()


if __name__ == "__main__":
    main()
