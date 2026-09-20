# Provider Deploy Subverbs

> 40 nodes · cohesion 0.07

## Key Concepts

- **._run_cdk()** (14 connections) — `deploy_aws/gherkai_deploy_aws/cli.py`
- **.deploy()** (9 connections) — `deploy_aws/gherkai_deploy_aws/cli.py`
- **._resolve_target_or_report()** (9 connections) — `deploy_aws/gherkai_deploy_aws/cli.py`
- **.bootstrap()** (8 connections) — `deploy_aws/gherkai_deploy_aws/cli.py`
- **._require_vpc()** (7 connections) — `deploy_aws/gherkai_deploy_aws/cli.py`
- **._resolve_version()** (7 connections) — `deploy_aws/gherkai_deploy_aws/cli.py`
- **.synth_only()** (7 connections) — `deploy_aws/gherkai_deploy_aws/cli.py`
- **._toolchain_gate()** (7 connections) — `deploy_aws/gherkai_deploy_aws/cli.py`
- **readonly_flag_conflict()** (6 connections) — `cli/gherkai_cli/deploy.py`
- **.build_context()** (6 connections) — `deploy_aws/gherkai_deploy_aws/cli.py`
- **._container_engine()** (5 connections) — `deploy_aws/gherkai_deploy_aws/cli.py`
- **.diff()** (5 connections) — `deploy_aws/gherkai_deploy_aws/cli.py`
- **.push_worker()** (5 connections) — `deploy_aws/gherkai_deploy_aws/cli.py`
- **._resolve_target()** (5 connections) — `deploy_aws/gherkai_deploy_aws/cli.py`
- **._work_dir()** (5 connections) — `deploy_aws/gherkai_deploy_aws/cli.py`
- **._worker_image_steps()** (5 connections) — `deploy_aws/gherkai_deploy_aws/cli.py`
- **.write_cdk_json()** (5 connections) — `deploy_aws/gherkai_deploy_aws/cli.py`
- **Path** (5 connections)
- **.app_command()** (4 connections) — `deploy_aws/gherkai_deploy_aws/cli.py`
- **.destroy()** (4 connections) — `deploy_aws/gherkai_deploy_aws/cli.py`
- **.list_workers()** (4 connections) — `deploy_aws/gherkai_deploy_aws/cli.py`
- **provider 子动词（`_deploy_verb`，worker 镜像族、会真写账户）与 `--diff/--synth-…** (1 connections) — `cli/gherkai_cli/deploy.py`
- **供给/更新后端。**先过 VPC 取值三态**（ADR 0037 决策 6），过了才调 `cdk deploy`。** (1 connections) — `deploy_aws/gherkai_deploy_aws/cli.py`
- **销毁 stack。**表/桶/ECR 是 `RETAIN`、不随之删**（防误删，ADR 0033）——残留清单见 README。 不过 VPC…** (1 connections) — `deploy_aws/gherkai_deploy_aws/cli.py`
- **只呈变更集（不改任何东西）。**它是 VPC 取值三态的指定核对手段**，故自身不做三态比对—— 对本机制之前部署的环境，`deploy` 以退出码 2…** (1 connections) — `deploy_aws/gherkai_deploy_aws/cli.py`
- *... and 15 more nodes in this community*

## Relationships

- [Deploy Provider Interface](Deploy_Provider_Interface.md) (19 shared connections)
- [Deploy CLI Doctor Checks](Deploy_CLI_Doctor_Checks.md) (9 shared connections)
- [Backend CDK Stack](Backend_CDK_Stack.md) (2 shared connections)
- [CDK Context Cache](CDK_Context_Cache.md) (2 shared connections)
- [Deploy Provider Resolution](Deploy_Provider_Resolution.md) (1 shared connections)
- [CLI Command Dispatch](CLI_Command_Dispatch.md) (1 shared connections)
- [Container Engine Adapter](Container_Engine_Adapter.md) (1 shared connections)

## Source Files

- `cli/gherkai_cli/deploy.py`
- `deploy_aws/gherkai_deploy_aws/cli.py`

## Audit Trail

- EXTRACTED: 88 (95%)
- INFERRED: 5 (5%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*