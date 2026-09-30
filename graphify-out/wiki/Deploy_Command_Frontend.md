# Deploy Command Frontend

> 7 nodes · cohesion 0.33

## Key Concepts

- **deploy.py** (10 connections) — `cli/gherkai_cli/deploy.py`
- **add_parsers()** (4 connections) — `cli/gherkai_cli/deploy.py`
- **_add_provider_flag()** (4 connections) — `cli/gherkai_cli/deploy.py`
- **ArgumentParser** (1 connections)
- **`gherkai deploy` / `gherkai destroy` 的命令行前端：provider 发现 + 命令面 flag，**不含任何 IaC…** (1 connections) — `cli/gherkai_cli/deploy.py`
- **把 `deploy` / `destroy` 两个子命令贴到主 parser 上；`provider` 已解析则让它贴自己的 flag。 解析结果经…** (1 connections) — `cli/gherkai_cli/deploy.py`
- **`--provider`：只在装了多个 provider 时必给（装一个时省略即用它，ADR 0037 决策 6）。** (1 connections) — `cli/gherkai_cli/deploy.py`

## Relationships

- [Provider Resolution and Doctor](Provider_Resolution_and_Doctor.md) (2 shared connections)
- [CLI Command Handlers](CLI_Command_Handlers.md) (1 shared connections)
- [Deploy Command Frontend Tests](Deploy_Command_Frontend_Tests.md) (1 shared connections)
- [CDK Command Wrapper](CDK_Command_Wrapper.md) (1 shared connections)
- [CLI Docs and ADRs](CLI_Docs_and_ADRs.md) (1 shared connections)
- [CDK App and Deploy CLI](CDK_App_and_Deploy_CLI.md) (1 shared connections)
- [CLI Parser Construction](CLI_Parser_Construction.md) (1 shared connections)

## Source Files

- `cli/gherkai_cli/deploy.py`

## Audit Trail

- EXTRACTED: 14 (93%)
- INFERRED: 1 (7%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*