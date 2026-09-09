# Provider Flag Wiring

> 15 nodes · cohesion 0.19

## Key Concepts

- **.add_arguments()** (8 connections) — `deploy_aws/gherkai_deploy_aws/cli.py`
- **._add_worker_subverbs()** (6 connections) — `deploy_aws/gherkai_deploy_aws/cli.py`
- **ArgumentParser** (6 connections)
- **._add_container_engine_flag()** (5 connections) — `deploy_aws/gherkai_deploy_aws/cli.py`
- **._add_locator_flags()** (4 connections) — `deploy_aws/gherkai_deploy_aws/cli.py`
- **._declares_worker_subverbs()** (4 connections) — `deploy_aws/gherkai_deploy_aws/cli.py`
- **._is_destroy_parser()** (4 connections) — `deploy_aws/gherkai_deploy_aws/cli.py`
- **_vpc_flag()** (3 connections) — `deploy_aws/gherkai_deploy_aws/cli.py`
- **`--vpc` 的取值校验：`default` / `new` / `vpc-<id>` 三档，**无隐式默认**（ADR 0037 决策 6； 三档与…** (1 connections) — `deploy_aws/gherkai_deploy_aws/cli.py`
- **把 provider 特有 flag 挂上 CLI 给的 parser。…** (1 connections) — `deploy_aws/gherkai_deploy_aws/cli.py`
- **这个 parser 是 **destroy** 的那个吗（`prog` 末段判，同 `_declares_worker_subverbs` 的口径）。** (1 connections) — `deploy_aws/gherkai_deploy_aws/cli.py`
- **这个 parser 是 **deploy** 的那个吗？ 皮对 deploy 与 destroy **各调一次** `add_arguments`（两者共用…** (1 connections) — `deploy_aws/gherkai_deploy_aws/cli.py`
- **`push-worker` / `list-workers` / `delete-worker` 三个子动词（ADR 0038）。…** (1 connections) — `deploy_aws/gherkai_deploy_aws/cli.py`
- **`--container-engine`（ADR 0038「容器引擎口子」）：这一期只 docker，别的名字退 2、不静默回落。** (1 connections) — `deploy_aws/gherkai_deploy_aws/cli.py`
- **子动词也收 `--prefix` / `--region` / `--profile`。 **`default=SUPPRESS`…** (1 connections) — `deploy_aws/gherkai_deploy_aws/cli.py`

## Relationships

- [AWS Deploy Provider CLI](AWS_Deploy_Provider_CLI.md) (6 shared connections)
- [CDK App & Deploy CLI](CDK_App_%26_Deploy_CLI.md) (1 shared connections)

## Source Files

- `deploy_aws/gherkai_deploy_aws/cli.py`

## Audit Trail

- EXTRACTED: 26 (96%)
- INFERRED: 1 (4%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*