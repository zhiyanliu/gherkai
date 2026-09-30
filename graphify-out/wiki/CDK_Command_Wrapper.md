# CDK Command Wrapper

> 37 nodes · cohesion 0.07

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
- **_make_sts_client()** (3 connections) — `deploy_aws/gherkai_deploy_aws/cli.py`
- **_node_major()** (3 connections) — `deploy_aws/gherkai_deploy_aws/cli.py`
- **test_cdk_command_prefers_path_cdk_then_npx()** (2 connections) — `deploy_aws/tests/test_provider.py`
- **test_node_too_old_is_rejected()** (2 connections) — `deploy_aws/tests/test_provider.py`
- **test_unparseable_node_version_does_not_block()** (2 connections) — `deploy_aws/tests/test_provider.py`
- **provider 子动词（`_deploy_verb`，worker 镜像族、会真写账户）与 `--diff/--synth-…** (1 connections) — `cli/gherkai_cli/deploy.py`
- **boto3 sts client（bootstrap 取 account id）。惰性 import：`--help` 不拉 boto3。** (1 connections) — `deploy_aws/gherkai_deploy_aws/cli.py`
- **销毁 stack。**表/桶/ECR 是 `RETAIN`、不随之删**（防误删，ADR 0033）——残留清单见 README。 不过 VPC…** (1 connections) — `deploy_aws/gherkai_deploy_aws/cli.py`
- **只呈变更集（不改任何东西）。**它是 VPC 取值三态的指定核对手段**，故自身不做三态比对—— 对本机制之前部署的环境，`deploy` 以退出码 2…** (1 connections) — `deploy_aws/gherkai_deploy_aws/cli.py`
- *... and 12 more nodes in this community*

## Relationships

- [AWS Deploy Provider](AWS_Deploy_Provider.md) (14 shared connections)
- [CDK App and Deploy CLI](CDK_App_and_Deploy_CLI.md) (6 shared connections)
- [Worker Deploy CLI](Worker_Deploy_CLI.md) (6 shared connections)
- [CDK Invocation Fakes](CDK_Invocation_Fakes.md) (2 shared connections)
- [Deploy/Destroy Dispatch](Deploy-Destroy_Dispatch.md) (1 shared connections)
- [Deploy Command Frontend](Deploy_Command_Frontend.md) (1 shared connections)
- [Container Engine Wrapper](Container_Engine_Wrapper.md) (1 shared connections)
- [Release Notes Tooling](Release_Notes_Tooling.md) (1 shared connections)

## Source Files

- `cli/gherkai_cli/deploy.py`
- `deploy_aws/gherkai_deploy_aws/cli.py`
- `deploy_aws/tests/test_provider.py`

## Audit Trail

- EXTRACTED: 76 (95%)
- INFERRED: 4 (5%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*