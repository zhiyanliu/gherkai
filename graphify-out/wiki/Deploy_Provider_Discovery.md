# Deploy Provider Discovery

> 14 nodes · cohesion 0.16

## Key Concepts

- **deploy.py** (10 connections) — `cli/gherkai_cli/deploy.py`
- **resolve_provider()** (6 connections) — `cli/gherkai_cli/deploy.py`
- **add_parsers()** (4 connections) — `cli/gherkai_cli/deploy.py`
- **_add_provider_flag()** (4 connections) — `cli/gherkai_cli/deploy.py`
- **provider_entry_points()** (4 connections) — `cli/gherkai_cli/deploy.py`
- **_peek_deploy_provider()** (4 connections) — `cli/gherkai_cli/__main__.py`
- **ArgumentParser** (1 connections)
- **`gherkai deploy` / `gherkai destroy` 的命令皮：provider 发现 + 命令面 flag，**不含任何 IaC…** (1 connections) — `cli/gherkai_cli/deploy.py`
- **`--provider`：只在装了多个 provider 时必给（装一个时省略即用它，ADR 0037 决策 6）。** (1 connections) — `cli/gherkai_cli/deploy.py`
- **已装的 provider entry point（按名排序、**不加载**）——零个/一个/多个的分叉全据此判。** (1 connections) — `cli/gherkai_cli/deploy.py`
- **按 `--provider` 值（或唯一性）选出 provider 并加载 → `(provider, None)`；失败 → `(None,…** (1 connections) — `cli/gherkai_cli/deploy.py`
- **把 `deploy` / `destroy` 两个子命令贴到主 parser 上；`provider` 已解析则让它贴自己的 flag。 解析结果经…** (1 connections) — `cli/gherkai_cli/deploy.py`
- **从 argv 窥出「是不是 deploy/destroy、有没有 --provider」，据此解析部署 provider（ADR 0037 决策 6）。…** (1 connections) — `cli/gherkai_cli/__main__.py`
- **EntryPoint** (1 connections)

## Relationships

- [CLI Main Entry](CLI_Main_Entry.md) (3 shared connections)
- [Deploy Command Shell](Deploy_Command_Shell.md) (2 shared connections)
- [CI & Release Workflows](CI_%26_Release_Workflows.md) (1 shared connections)
- [CDK App & Deploy CLI](CDK_App_%26_Deploy_CLI.md) (1 shared connections)
- [Architecture Decision Records](Architecture_Decision_Records.md) (1 shared connections)
- [Deploy/Destroy Provider Dispatch](Deploy-Destroy_Provider_Dispatch.md) (1 shared connections)
- [CLI Run Entry Tests](CLI_Run_Entry_Tests.md) (1 shared connections)

## Source Files

- `cli/gherkai_cli/__main__.py`
- `cli/gherkai_cli/deploy.py`

## Audit Trail

- EXTRACTED: 25 (100%)
- INFERRED: 0 (0%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*