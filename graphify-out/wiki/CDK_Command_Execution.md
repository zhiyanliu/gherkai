# CDK Command Execution

> 33 nodes · cohesion 0.08

## Key Concepts

- **._run_cdk()** (14 connections) — `deploy_aws/gherkai_deploy_aws/cli.py`
- **.bootstrap()** (8 connections) — `deploy_aws/gherkai_deploy_aws/cli.py`
- **cdk_command()** (7 connections) — `deploy_aws/gherkai_deploy_aws/cli.py`
- **check_node()** (7 connections) — `deploy_aws/gherkai_deploy_aws/cli.py`
- **._require_vpc()** (7 connections) — `deploy_aws/gherkai_deploy_aws/cli.py`
- **.synth_only()** (7 connections) — `deploy_aws/gherkai_deploy_aws/cli.py`
- **._toolchain_gate()** (7 connections) — `deploy_aws/gherkai_deploy_aws/cli.py`
- **readonly_flag_conflict()** (6 connections) — `cli/gherkai_cli/deploy.py`
- **.diff()** (5 connections) — `deploy_aws/gherkai_deploy_aws/cli.py`
- **.doctor()** (5 connections) — `deploy_aws/gherkai_deploy_aws/cli.py`
- **._work_dir()** (5 connections) — `deploy_aws/gherkai_deploy_aws/cli.py`
- **.write_cdk_json()** (5 connections) — `deploy_aws/gherkai_deploy_aws/cli.py`
- **Path** (5 connections)
- **check_cdk()** (4 connections) — `deploy_aws/gherkai_deploy_aws/cli.py`
- **.app_command()** (4 connections) — `deploy_aws/gherkai_deploy_aws/cli.py`
- **.destroy()** (4 connections) — `deploy_aws/gherkai_deploy_aws/cli.py`
- **test_cdk_command_prefers_path_cdk_then_npx()** (2 connections) — `deploy_aws/tests/test_provider.py`
- **test_node_too_old_is_rejected()** (2 connections) — `deploy_aws/tests/test_provider.py`
- **test_unparseable_node_version_does_not_block()** (2 connections) — `deploy_aws/tests/test_provider.py`
- **provider 子动词（`_deploy_verb`，worker 镜像族、会真写账户）与 `--diff/--synth-…** (1 connections) — `cli/gherkai_cli/deploy.py`
- **销毁 stack。**表/桶/ECR 是 `RETAIN`、不随之删**（防误删，ADR 0033）——残留清单见 README。 不过 VPC…** (1 connections) — `deploy_aws/gherkai_deploy_aws/cli.py`
- **只呈变更集（不改任何东西）。**它是 VPC 取值三态的指定核对手段**，故自身不做三态比对—— 对本机制之前部署的环境，`deploy` 以退出码 2…** (1 connections) — `deploy_aws/gherkai_deploy_aws/cli.py`
- **导出 CloudFormation 模板到 `args.synth_only`（escape valve：不让 0.x 工具改自己生产账号的 reviewer…** (1 connections) — `deploy_aws/gherkai_deploy_aws/cli.py`
- **`cdk bootstrap`（首次在某 account/region 用 CDK 的前置）——**账户级动作，不合成 app、不需要 `--vpc`**。…** (1 connections) — `deploy_aws/gherkai_deploy_aws/cli.py`
- **`gherkai doctor` 的 provider 段（ADR 0041 决策四）：部署方工具链**只读**自检——Node ≥ 22、cdk…** (1 connections) — `deploy_aws/gherkai_deploy_aws/cli.py`
- *... and 8 more nodes in this community*

## Relationships

- [Deploy Provider & Container Seam](Deploy_Provider_%26_Container_Seam.md) (14 shared connections)
- [Deploy Provider Commands](Deploy_Provider_Commands.md) (7 shared connections)
- [CDK App & AWS Provider CLI](CDK_App_%26_AWS_Provider_CLI.md) (5 shared connections)
- [CDK Context Cache](CDK_Context_Cache.md) (2 shared connections)
- [CLI Command Dispatch Entry](CLI_Command_Dispatch_Entry.md) (1 shared connections)
- [Deploy CLI Provider Discovery](Deploy_CLI_Provider_Discovery.md) (1 shared connections)
- [Container Engine Port](Container_Engine_Port.md) (1 shared connections)
- [Worker Job Source Input](Worker_Job_Source_Input.md) (1 shared connections)

## Source Files

- `cli/gherkai_cli/deploy.py`
- `deploy_aws/gherkai_deploy_aws/cli.py`
- `deploy_aws/tests/test_provider.py`

## Audit Trail

- EXTRACTED: 72 (95%)
- INFERRED: 4 (5%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*