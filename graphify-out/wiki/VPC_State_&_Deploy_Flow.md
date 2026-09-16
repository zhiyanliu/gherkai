# VPC State & Deploy Flow

> 24 nodes · cohesion 0.11

## Key Concepts

- **.deploy()** (9 connections) — `deploy_aws/gherkai_deploy_aws/cli.py`
- **._guard_vpc_spec()** (9 connections) — `deploy_aws/gherkai_deploy_aws/cli.py`
- **._resolve_target()** (9 connections) — `deploy_aws/gherkai_deploy_aws/cli.py`
- **classify_vpc_state()** (7 connections) — `deploy_aws/gherkai_deploy_aws/cli.py`
- **._resolve_version()** (7 connections) — `deploy_aws/gherkai_deploy_aws/cli.py`
- **.build_context()** (6 connections) — `deploy_aws/gherkai_deploy_aws/cli.py`
- **._container_engine()** (5 connections) — `deploy_aws/gherkai_deploy_aws/cli.py`
- **.push_worker()** (5 connections) — `deploy_aws/gherkai_deploy_aws/cli.py`
- **._worker_image_steps()** (5 connections) — `deploy_aws/gherkai_deploy_aws/cli.py`
- **vpc_spec_matches()** (5 connections) — `deploy_aws/gherkai_deploy_aws/cli.py`
- **.list_workers()** (4 connections) — `deploy_aws/gherkai_deploy_aws/cli.py`
- **test_classify_four_states()** (2 connections) — `deploy_aws/tests/test_provider.py`
- **test_classify_stack_absent_is_first_deploy_even_without_param()** (2 connections) — `deploy_aws/tests/test_provider.py`
- **三态判定（ADR 0037 决策 6）。返回上面四个 `VPC_*` 之一。 判序里 **stack…** (1 connections) — `deploy_aws/gherkai_deploy_aws/cli.py`
- **供给/更新后端。**先过 VPC 档三态**（ADR 0037 决策 6），过了才调 `cdk deploy`。** (1 connections) — `deploy_aws/gherkai_deploy_aws/cli.py`
- **`gherkai deploy push-worker <镜像> --engine … --variant …`（八步见…** (1 connections) — `deploy_aws/gherkai_deploy_aws/cli.py`
- **`gherkai deploy list-workers`——只读（SSM + ECS describe），不碰容器引擎。** (1 connections) — `deploy_aws/gherkai_deploy_aws/cli.py`
- **解析 `--container-engine` / env → 引擎对象；本期未实装的名字 → 打诊断并返回 None（调用点退 2）。…** (1 connections) — `deploy_aws/gherkai_deploy_aws/cli.py`
- **cdk 成功之后的 worker 镜像第 2/3/4 步 + 清理 pass（第 1 步是 stack 资源、随 cdk 事务）。 `engine` 由…** (1 connections) — `deploy_aws/gherkai_deploy_aws/cli.py`
- **flag → CDK context（app/stack 侧读的那四个旋钮 + 版本戳）。 `--vpc` 一个 flag 摊成两个旋钮：`default`…** (1 connections) — `deploy_aws/gherkai_deploy_aws/cli.py`
- **deploy 前的 VPC 档比对。放行 → None；拦 → 退出码（2）。 只在 deploy 前跑（见 `diff`/`destroy` 的…** (1 connections) — `deploy_aws/gherkai_deploy_aws/cli.py`
- **prefix / region / profile 走产品本体的**同一条解析链**（`compose.resolve_cloud_target`，ADR…** (1 connections) — `deploy_aws/gherkai_deploy_aws/cli.py`
- **写进 SSM 版本戳的版本（ADR 0037 决策 6「版本戳」/ 决策 7 版本单旋钮）。 优先 CLI 皮交进来的 `args.version`（=…** (1 connections) — `deploy_aws/gherkai_deploy_aws/cli.py`
- **SSM 里记的生效档 `stored` 是否 == 本次 `--vpc requested`。 三档形态见…** (1 connections) — `deploy_aws/gherkai_deploy_aws/cli.py`

## Relationships

- [AWS Deploy Provider](AWS_Deploy_Provider.md) (13 shared connections)
- [CDK App & AWS Provider CLI](CDK_App_%26_AWS_Provider_CLI.md) (6 shared connections)
- [Deploy Provider Tests](Deploy_Provider_Tests.md) (5 shared connections)
- [CDK Toolchain Preflight](CDK_Toolchain_Preflight.md) (2 shared connections)
- [Backend CDK Stack](Backend_CDK_Stack.md) (1 shared connections)
- [Container Engine Adapter](Container_Engine_Adapter.md) (1 shared connections)

## Source Files

- `deploy_aws/gherkai_deploy_aws/cli.py`
- `deploy_aws/tests/test_provider.py`

## Audit Trail

- EXTRACTED: 56 (98%)
- INFERRED: 1 (2%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*