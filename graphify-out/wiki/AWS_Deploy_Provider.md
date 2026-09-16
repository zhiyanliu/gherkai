# AWS Deploy Provider

> 32 nodes · cohesion 0.09

## Key Concepts

- **Provider** (89 connections) — `deploy_aws/gherkai_deploy_aws/cli.py`
- **._run_cdk()** (14 connections) — `deploy_aws/gherkai_deploy_aws/cli.py`
- **.synth_only()** (7 connections) — `deploy_aws/gherkai_deploy_aws/cli.py`
- **._require_vpc()** (6 connections) — `deploy_aws/gherkai_deploy_aws/cli.py`
- **.diff()** (5 connections) — `deploy_aws/gherkai_deploy_aws/cli.py`
- **._work_dir()** (5 connections) — `deploy_aws/gherkai_deploy_aws/cli.py`
- **.write_cdk_json()** (5 connections) — `deploy_aws/gherkai_deploy_aws/cli.py`
- **Path** (5 connections)
- **.app_command()** (4 connections) — `deploy_aws/gherkai_deploy_aws/cli.py`
- **.destroy()** (4 connections) — `deploy_aws/gherkai_deploy_aws/cli.py`
- **test_contributed_flag_surface_is_exactly_the_provider_specific_set()** (3 connections) — `deploy_aws/tests/test_provider.py`
- **test_provider_doctor_reports_toolchain()** (3 connections) — `deploy_aws/tests/test_provider.py`
- **test_the_two_action_knobs_are_only_on_deploy()** (3 connections) — `deploy_aws/tests/test_provider.py`
- **test_worker_subverb_surface_is_exactly_three_and_only_on_deploy()** (3 connections) — `deploy_aws/tests/test_provider.py`
- **.delete_worker()** (2 connections) — `deploy_aws/gherkai_deploy_aws/cli.py`
- **test_app_command_uses_current_interpreter_and_module()** (2 connections) — `deploy_aws/tests/test_provider.py`
- **test_generated_cdk_json_carries_app_and_feature_flags_verbatim()** (2 connections) — `deploy_aws/tests/test_provider.py`
- **test_provider_name_is_aws()** (2 connections) — `deploy_aws/tests/test_provider.py`
- **test_yes_is_destroy_only()** (2 connections) — `deploy_aws/tests/test_provider.py`
- **AWS provider——`gherkai deploy` 族命令在 AWS 上的实现（接缝契约见模块头）。** (1 connections) — `deploy_aws/gherkai_deploy_aws/cli.py`
- **销毁 stack。**表/桶/ECR 是 `RETAIN`、不随之删**（防误删，ADR 0033）——残留清单见 README。 不过 VPC…** (1 connections) — `deploy_aws/gherkai_deploy_aws/cli.py`
- **只呈变更集（不改任何东西）。**它是 VPC 档三态的指定核对手段**，故自身不做三态比对—— 对本机制之前部署的环境，`deploy` 退 2…** (1 connections) — `deploy_aws/gherkai_deploy_aws/cli.py`
- **导出 CloudFormation 模板到 `args.synth_only`（escape valve：不让 0.x 工具改自己生产账号的 reviewer…** (1 connections) — `deploy_aws/gherkai_deploy_aws/cli.py`
- **留的口子（ADR 0038「命令族」）：**尚未提供**，退 2 说清为什么与将来怎么落。 为何占位而不干脆不给这个子命令：不给的话用户敲了只会得到…** (1 connections) — `deploy_aws/gherkai_deploy_aws/cli.py`
- **凡要合成 app 的动作（deploy / diff / synth / destroy）都必须有 `--vpc`（无隐式默认，ADR 0037 决策 6）；…** (1 connections) — `deploy_aws/gherkai_deploy_aws/cli.py`
- *... and 7 more nodes in this community*

## Relationships

- [Deploy Provider Tests](Deploy_Provider_Tests.md) (36 shared connections)
- [VPC State & Deploy Flow](VPC_State_%26_Deploy_Flow.md) (13 shared connections)
- [CDK Bootstrap/Destroy CLI](CDK_Bootstrap-Destroy_CLI.md) (7 shared connections)
- [CDK Context Cache](CDK_Context_Cache.md) (6 shared connections)
- [Provider CLI Flags](Provider_CLI_Flags.md) (6 shared connections)
- [CDK Toolchain Preflight](CDK_Toolchain_Preflight.md) (6 shared connections)
- [Deploy CLI Test Doubles](Deploy_CLI_Test_Doubles.md) (5 shared connections)
- [CloudFormation/SSM Test Doubles](CloudFormation-SSM_Test_Doubles.md) (3 shared connections)
- [Container Engine Absence Warning](Container_Engine_Absence_Warning.md) (2 shared connections)
- [Skill Deploy Token Guardrail](Skill_Deploy_Token_Guardrail.md) (2 shared connections)
- [Deploy Command Parsers](Deploy_Command_Parsers.md) (2 shared connections)
- [CDK App & AWS Provider CLI](CDK_App_%26_AWS_Provider_CLI.md) (1 shared connections)

## Source Files

- `deploy_aws/gherkai_deploy_aws/cli.py`
- `deploy_aws/tests/test_provider.py`

## Audit Trail

- EXTRACTED: 124 (92%)
- INFERRED: 11 (8%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*