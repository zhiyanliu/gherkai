# CDK Command Orchestration

> 39 nodes · cohesion 0.07

## Key Concepts

- **._run_cdk()** (14 connections) — `deploy_aws/gherkai_deploy_aws/cli.py`
- **._resolve_target()** (9 connections) — `deploy_aws/gherkai_deploy_aws/cli.py`
- **.deploy()** (8 connections) — `deploy_aws/gherkai_deploy_aws/cli.py`
- **.bootstrap()** (7 connections) — `deploy_aws/gherkai_deploy_aws/cli.py`
- **.build_context()** (6 connections) — `deploy_aws/gherkai_deploy_aws/cli.py`
- **._container_engine()** (6 connections) — `deploy_aws/gherkai_deploy_aws/cli.py`
- **._require_vpc()** (6 connections) — `deploy_aws/gherkai_deploy_aws/cli.py`
- **._resolve_version()** (6 connections) — `deploy_aws/gherkai_deploy_aws/cli.py`
- **.synth_only()** (6 connections) — `deploy_aws/gherkai_deploy_aws/cli.py`
- **._worker_image_steps()** (6 connections) — `deploy_aws/gherkai_deploy_aws/cli.py`
- **cdk_command()** (5 connections) — `deploy_aws/gherkai_deploy_aws/cli.py`
- **.push_worker()** (5 connections) — `deploy_aws/gherkai_deploy_aws/cli.py`
- **._work_dir()** (5 connections) — `deploy_aws/gherkai_deploy_aws/cli.py`
- **.write_cdk_json()** (5 connections) — `deploy_aws/gherkai_deploy_aws/cli.py`
- **Path** (5 connections)
- **.app_command()** (4 connections) — `deploy_aws/gherkai_deploy_aws/cli.py`
- **.destroy()** (4 connections) — `deploy_aws/gherkai_deploy_aws/cli.py`
- **.diff()** (4 connections) — `deploy_aws/gherkai_deploy_aws/cli.py`
- **.list_workers()** (4 connections) — `deploy_aws/gherkai_deploy_aws/cli.py`
- **_make_sts_client()** (3 connections) — `deploy_aws/gherkai_deploy_aws/cli.py`
- **test_cdk_command_prefers_path_cdk_then_npx()** (2 connections) — `deploy_aws/tests/test_provider.py`
- **boto3 sts client（bootstrap 取 account id）。惰性 import：`--help` 不拉 boto3。** (1 connections) — `deploy_aws/gherkai_deploy_aws/cli.py`
- **供给/更新后端。**先过 VPC 档三态**（ADR 0037 决策 6），过了才调 `cdk deploy`。** (1 connections) — `deploy_aws/gherkai_deploy_aws/cli.py`
- **销毁 stack。**表/桶/ECR 是 `RETAIN`、不随之删**（防误删，ADR 0033）——残留清单见 README。 不过 VPC…** (1 connections) — `deploy_aws/gherkai_deploy_aws/cli.py`
- **只呈变更集（不改任何东西）。**它是 VPC 档三态的指定核对手段**，故自身不做三态比对—— 对本机制之前部署的环境，`deploy` 退 2…** (1 connections) — `deploy_aws/gherkai_deploy_aws/cli.py`
- *... and 14 more nodes in this community*

## Relationships

- [AWS Deploy Provider CLI](AWS_Deploy_Provider_CLI.md) (18 shared connections)
- [CDK App & Deploy CLI](CDK_App_%26_Deploy_CLI.md) (7 shared connections)
- [Environment and Version Resolution](Environment_and_Version_Resolution.md) (2 shared connections)
- [CDK Context Cache](CDK_Context_Cache.md) (2 shared connections)
- [Container Engine Adapter](Container_Engine_Adapter.md) (1 shared connections)

## Source Files

- `deploy_aws/gherkai_deploy_aws/cli.py`
- `deploy_aws/tests/test_provider.py`

## Audit Trail

- EXTRACTED: 82 (98%)
- INFERRED: 2 (2%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*