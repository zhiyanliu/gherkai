# Provider CLI Flags

> 13 nodes · cohesion 0.23

## Key Concepts

- **.add_arguments()** (8 connections) — `deploy_aws/gherkai_deploy_aws/cli.py`
- **._add_worker_subverbs()** (6 connections) — `deploy_aws/gherkai_deploy_aws/cli.py`
- **ArgumentParser** (6 connections)
- **._add_container_engine_flag()** (5 connections) — `deploy_aws/gherkai_deploy_aws/cli.py`
- **._add_locator_flags()** (4 connections) — `deploy_aws/gherkai_deploy_aws/cli.py`
- **._declares_worker_subverbs()** (4 connections) — `deploy_aws/gherkai_deploy_aws/cli.py`
- **._is_destroy_parser()** (4 connections) — `deploy_aws/gherkai_deploy_aws/cli.py`
- **把 provider 特有 flag 挂上 CLI 给的 parser。…** (1 connections) — `deploy_aws/gherkai_deploy_aws/cli.py`
- **这个 parser 是 **destroy** 的那个吗（`prog` 末段判，同 `_declares_worker_subverbs` 的口径）。** (1 connections) — `deploy_aws/gherkai_deploy_aws/cli.py`
- **这个 parser 是 **deploy** 的那个吗？ 前端对 deploy 与 destroy **各调一次** `add_arguments`（两者共用…** (1 connections) — `deploy_aws/gherkai_deploy_aws/cli.py`
- **`push-worker` / `list-workers` / `delete-worker` 三个子动词（ADR 0038）。…** (1 connections) — `deploy_aws/gherkai_deploy_aws/cli.py`
- **`--container-engine`（ADR 0038「容器引擎口子」）：这一期只 docker，别的名字以退出码 2 结束、不静默回落。** (1 connections) — `deploy_aws/gherkai_deploy_aws/cli.py`
- **子动词也收 `--prefix` / `--region` / `--profile`。 **`default=SUPPRESS`…** (1 connections) — `deploy_aws/gherkai_deploy_aws/cli.py`

## Relationships

- [Deploy Provider Interface](Deploy_Provider_Interface.md) (6 shared connections)
- [Deploy CLI Doctor Checks](Deploy_CLI_Doctor_Checks.md) (1 shared connections)

## Source Files

- `deploy_aws/gherkai_deploy_aws/cli.py`

## Audit Trail

- EXTRACTED: 24 (96%)
- INFERRED: 1 (4%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*