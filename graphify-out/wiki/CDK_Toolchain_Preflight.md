# CDK Toolchain Preflight

> 15 nodes · cohesion 0.15

## Key Concepts

- **.bootstrap()** (8 connections) — `deploy_aws/gherkai_deploy_aws/cli.py`
- **cdk_command()** (7 connections) — `deploy_aws/gherkai_deploy_aws/cli.py`
- **check_node()** (7 connections) — `deploy_aws/gherkai_deploy_aws/cli.py`
- **._toolchain_gate()** (7 connections) — `deploy_aws/gherkai_deploy_aws/cli.py`
- **.doctor()** (5 connections) — `deploy_aws/gherkai_deploy_aws/cli.py`
- **check_cdk()** (4 connections) — `deploy_aws/gherkai_deploy_aws/cli.py`
- **test_cdk_command_prefers_path_cdk_then_npx()** (2 connections) — `deploy_aws/tests/test_provider.py`
- **test_node_too_old_is_rejected()** (2 connections) — `deploy_aws/tests/test_provider.py`
- **test_unparseable_node_version_does_not_block()** (2 connections) — `deploy_aws/tests/test_provider.py`
- **`cdk bootstrap`（首次在某 account/region 用 CDK 的前置）——**账户级动作，不合成 app、不需要 `--vpc`**。…** (1 connections) — `deploy_aws/gherkai_deploy_aws/cli.py`
- **`gherkai doctor` 的 provider 段（ADR 0041 决策四）：部署方工具链**只读**自检——Node ≥ 22、cdk…** (1 connections) — `deploy_aws/gherkai_deploy_aws/cli.py`
- **Node 与 cdk CLI 两个前置：缺 → 打一句话、退 2；齐 → None。 `deploy` / `bootstrap` / `_run_cdk`…** (1 connections) — `deploy_aws/gherkai_deploy_aws/cli.py`
- **cdk CLI 的调用前缀：PATH 上的 `cdk` 优先，否则 `npx -y aws-cdk@2`（ADR 0037 决策 6）。都没有 → 空列表。** (1 connections) — `deploy_aws/gherkai_deploy_aws/cli.py`
- **cdk CLI 前置：PATH 上既无 `cdk` 也无 `npx` → 返回给人看的一句话；能定位 → None。 与 `check_node()`…** (1 connections) — `deploy_aws/gherkai_deploy_aws/cli.py`
- **Node 前置：缺失/过低 → 返回给人看的一句话；OK → None。**不抛 traceback**（ADR 0037 决策 6）。 为何必查：`aws-…** (1 connections) — `deploy_aws/gherkai_deploy_aws/cli.py`

## Relationships

- [AWS Deploy Provider](AWS_Deploy_Provider.md) (6 shared connections)
- [CDK App & AWS Provider CLI](CDK_App_%26_AWS_Provider_CLI.md) (5 shared connections)
- [Deploy Provider Tests](Deploy_Provider_Tests.md) (3 shared connections)
- [VPC State & Deploy Flow](VPC_State_%26_Deploy_Flow.md) (2 shared connections)
- [Deploy Command Parsers](Deploy_Command_Parsers.md) (1 shared connections)
- [Container Engine Adapter](Container_Engine_Adapter.md) (1 shared connections)

## Source Files

- `deploy_aws/gherkai_deploy_aws/cli.py`
- `deploy_aws/tests/test_provider.py`

## Audit Trail

- EXTRACTED: 33 (97%)
- INFERRED: 1 (3%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*