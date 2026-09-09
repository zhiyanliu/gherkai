# Provider Deploy Commands

> 32 nodes · cohesion 0.09

## Key Concepts

- **._run_cdk()** (14 connections) — `deploy_aws/gherkai_deploy_aws/cli.py`
- **._resolve_target()** (9 connections) — `deploy_aws/gherkai_deploy_aws/cli.py`
- **.deploy()** (8 connections) — `deploy_aws/gherkai_deploy_aws/cli.py`
- **.build_context()** (6 connections) — `deploy_aws/gherkai_deploy_aws/cli.py`
- **._container_engine()** (6 connections) — `deploy_aws/gherkai_deploy_aws/cli.py`
- **._require_vpc()** (6 connections) — `deploy_aws/gherkai_deploy_aws/cli.py`
- **._resolve_version()** (6 connections) — `deploy_aws/gherkai_deploy_aws/cli.py`
- **.synth_only()** (6 connections) — `deploy_aws/gherkai_deploy_aws/cli.py`
- **._worker_image_steps()** (6 connections) — `deploy_aws/gherkai_deploy_aws/cli.py`
- **.push_worker()** (5 connections) — `deploy_aws/gherkai_deploy_aws/cli.py`
- **._work_dir()** (5 connections) — `deploy_aws/gherkai_deploy_aws/cli.py`
- **.write_cdk_json()** (5 connections) — `deploy_aws/gherkai_deploy_aws/cli.py`
- **Path** (5 connections)
- **.app_command()** (4 connections) — `deploy_aws/gherkai_deploy_aws/cli.py`
- **.destroy()** (4 connections) — `deploy_aws/gherkai_deploy_aws/cli.py`
- **.diff()** (4 connections) — `deploy_aws/gherkai_deploy_aws/cli.py`
- **.list_workers()** (4 connections) — `deploy_aws/gherkai_deploy_aws/cli.py`
- **供给/更新后端。**先过 VPC 档三态**（ADR 0037 决策 6），过了才调 `cdk deploy`。** (1 connections) — `deploy_aws/gherkai_deploy_aws/cli.py`
- **销毁 stack。**表/桶/ECR 是 `RETAIN`、不随之删**（防误删，ADR 0033）——残留清单见 README。 不过 VPC…** (1 connections) — `deploy_aws/gherkai_deploy_aws/cli.py`
- **只呈变更集（不改任何东西）。**它是 VPC 档三态的指定核对手段**，故自身不做三态比对—— 对本机制之前部署的环境，`deploy` 退 2…** (1 connections) — `deploy_aws/gherkai_deploy_aws/cli.py`
- **导出 CloudFormation 模板到 `args.synth_only`（escape valve：不让 0.x 工具改自己生产账号的 reviewer…** (1 connections) — `deploy_aws/gherkai_deploy_aws/cli.py`
- **`gherkai deploy push-worker <镜像> --engine … --variant …`（八步见…** (1 connections) — `deploy_aws/gherkai_deploy_aws/cli.py`
- **`gherkai deploy list-workers`——只读（SSM + ECS describe），不碰容器引擎。** (1 connections) — `deploy_aws/gherkai_deploy_aws/cli.py`
- **解析 `--container-engine` / env → 引擎对象；本期未实装的名字 → 打诊断并返回 None（调用点退 2）。…** (1 connections) — `deploy_aws/gherkai_deploy_aws/cli.py`
- **cdk 成功之后的 worker 镜像第 2/3/4 步 + 清理 pass（第 1 步是 stack 资源、随 cdk 事务）。 **不做版本 skew…** (1 connections) — `deploy_aws/gherkai_deploy_aws/cli.py`
- *... and 7 more nodes in this community*

## Relationships

- [AWS Deploy Provider](AWS_Deploy_Provider.md) (16 shared connections)
- [CDK App & Deploy CLI](CDK_App_%26_Deploy_CLI.md) (7 shared connections)
- [Env Config & Error Classification](Env_Config_%26_Error_Classification.md) (2 shared connections)
- [CDK Context Cache](CDK_Context_Cache.md) (2 shared connections)
- [Container Engine Adapter](Container_Engine_Adapter.md) (1 shared connections)

## Source Files

- `deploy_aws/gherkai_deploy_aws/cli.py`

## Audit Trail

- EXTRACTED: 71 (97%)
- INFERRED: 2 (3%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*