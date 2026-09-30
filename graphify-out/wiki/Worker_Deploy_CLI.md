# Worker Deploy CLI

> 18 nodes · cohesion 0.14

## Key Concepts

- **.deploy()** (9 connections) — `deploy_aws/gherkai_deploy_aws/cli.py`
- **._resolve_target_or_report()** (9 connections) — `deploy_aws/gherkai_deploy_aws/cli.py`
- **._resolve_version()** (7 connections) — `deploy_aws/gherkai_deploy_aws/cli.py`
- **.build_context()** (6 connections) — `deploy_aws/gherkai_deploy_aws/cli.py`
- **._container_engine()** (5 connections) — `deploy_aws/gherkai_deploy_aws/cli.py`
- **.push_worker()** (5 connections) — `deploy_aws/gherkai_deploy_aws/cli.py`
- **._resolve_target()** (5 connections) — `deploy_aws/gherkai_deploy_aws/cli.py`
- **._worker_image_steps()** (5 connections) — `deploy_aws/gherkai_deploy_aws/cli.py`
- **.list_workers()** (4 connections) — `deploy_aws/gherkai_deploy_aws/cli.py`
- **供给/更新后端。**先过 VPC 取值三态**（ADR 0037 决策 6），过了才调 `cdk deploy`。** (1 connections) — `deploy_aws/gherkai_deploy_aws/cli.py`
- **`gherkai deploy push-worker <镜像> --engine … --variant …`（八步见…** (1 connections) — `deploy_aws/gherkai_deploy_aws/cli.py`
- **`gherkai deploy list-workers`——只读（SSM + ECS describe），不碰容器引擎。** (1 connections) — `deploy_aws/gherkai_deploy_aws/cli.py`
- **解析 `--container-engine` / env → 引擎对象；本期未实装的名字 → 打诊断并返回 None（调用点以退出码 2 结束）。…** (1 connections) — `deploy_aws/gherkai_deploy_aws/cli.py`
- **cdk 成功之后的 worker 镜像第 2/3/4 步 + 清理 pass（第 1 步是 stack 资源、随 cdk 事务）。 `engine` 由…** (1 connections) — `deploy_aws/gherkai_deploy_aws/cli.py`
- **flag → CDK context（app/stack 侧读的那四个配置项 + 版本戳）。 `--vpc` 一个 flag…** (1 connections) — `deploy_aws/gherkai_deploy_aws/cli.py`
- **prefix / region / profile 走产品本体的**同一条解析链**（`compose.resolve_cloud_target`，ADR…** (1 connections) — `deploy_aws/gherkai_deploy_aws/cli.py`
- **解析链的诊断归口：解析得出 → target；失败 → 打一句诊断、返 None（调用点归退出码）。 **每个动作在碰 AWS 之前都要经这一口**：不存在的…** (1 connections) — `deploy_aws/gherkai_deploy_aws/cli.py`
- **写进 SSM 版本戳的版本（ADR 0037 决策 6「版本戳」/ 决策 7 版本真源）。 优先 CLI 前端交进来的…** (1 connections) — `deploy_aws/gherkai_deploy_aws/cli.py`

## Relationships

- [AWS Deploy Provider](AWS_Deploy_Provider.md) (9 shared connections)
- [CDK Command Wrapper](CDK_Command_Wrapper.md) (6 shared connections)
- [CDK App and Deploy CLI](CDK_App_and_Deploy_CLI.md) (3 shared connections)
- [Release Notes Tooling](Release_Notes_Tooling.md) (1 shared connections)
- [Container Engine Wrapper](Container_Engine_Wrapper.md) (1 shared connections)

## Source Files

- `deploy_aws/gherkai_deploy_aws/cli.py`

## Audit Trail

- EXTRACTED: 41 (98%)
- INFERRED: 1 (2%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*