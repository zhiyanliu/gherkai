# Deploy Command Parsers

> 24 nodes · cohesion 0.10

## Key Concepts

- **deploy.py** (8 connections) — `cli/gherkai_cli/deploy.py`
- **resolve_provider()** (7 connections) — `cli/gherkai_cli/deploy.py`
- **readonly_flag_conflict()** (6 connections) — `cli/gherkai_cli/deploy.py`
- **_cmd_deploy()** (6 connections) — `cli/gherkai_cli/__main__.py`
- **_deploy_provider()** (6 connections) — `cli/gherkai_cli/__main__.py`
- **provider_entry_points()** (5 connections) — `cli/gherkai_cli/deploy.py`
- **_doctor_provider()** (5 connections) — `cli/gherkai_cli/__main__.py`
- **add_parsers()** (4 connections) — `cli/gherkai_cli/deploy.py`
- **_add_provider_flag()** (4 connections) — `cli/gherkai_cli/deploy.py`
- **_cmd_destroy()** (4 connections) — `cli/gherkai_cli/__main__.py`
- **_peek_deploy_provider()** (4 connections) — `cli/gherkai_cli/__main__.py`
- **ArgumentParser** (1 connections)
- **`gherkai deploy` / `gherkai destroy` 的命令皮：provider 发现 + 命令面 flag，**不含任何 IaC…** (1 connections) — `cli/gherkai_cli/deploy.py`
- **把 `deploy` / `destroy` 两个子命令贴到主 parser 上；`provider` 已解析则让它贴自己的 flag。 解析结果经…** (1 connections) — `cli/gherkai_cli/deploy.py`
- **`--provider`：只在装了多个 provider 时必给（装一个时省略即用它，ADR 0037 决策 6）。** (1 connections) — `cli/gherkai_cli/deploy.py`
- **已装的 provider entry point（按名排序、**不加载**）——零个/一个/多个的分叉全据此判。** (1 connections) — `cli/gherkai_cli/deploy.py`
- **按 `--provider` 值（或唯一性）选出 provider 并加载 → `(provider, None)`；失败 → `(None,…** (1 connections) — `cli/gherkai_cli/deploy.py`
- **provider 子动词（`_deploy_verb`，worker 镜像族、会真写账户）与 `--diff/--synth-…** (1 connections) — `cli/gherkai_cli/deploy.py`
- **取已解析的 provider（`main` 窥 argv 时解析、经 `set_defaults` 落在 args 上）。 两个 None…** (1 connections) — `cli/gherkai_cli/__main__.py`
- **[部署方] 分派给 provider（ADR 0037 决策 6）：三个「不真部署」动作互斥，其余走真部署。皮零 IaC 知识。 退出码即 provider…** (1 connections) — `cli/gherkai_cli/__main__.py`
- **[部署方] 拆栈：分派给 provider（哪些资源 RETAIN 是 IaC 侧的事，ADR 0033）。** (1 connections) — `cli/gherkai_cli/__main__.py`
- **doctor 的 provider 段：按 entry point 结构化判「没装 / 装了多个 / 装了但坏 / 装了且可自检」，别靠匹配错误文案。…** (1 connections) — `cli/gherkai_cli/__main__.py`
- **从 argv 窥出「是不是 deploy/destroy、有没有 --provider」，据此解析部署 provider（ADR 0037 决策 6）。…** (1 connections) — `cli/gherkai_cli/__main__.py`
- **EntryPoint** (1 connections)

## Relationships

- [CLI Command Entry Points](CLI_Command_Entry_Points.md) (8 shared connections)
- [CLI Main Flow Tests](CLI_Main_Flow_Tests.md) (3 shared connections)
- [Deploy CLI Shell](Deploy_CLI_Shell.md) (2 shared connections)
- [AWS Deploy Provider](AWS_Deploy_Provider.md) (2 shared connections)
- [CLI Parser Construction](CLI_Parser_Construction.md) (1 shared connections)
- [CDK Toolchain Preflight](CDK_Toolchain_Preflight.md) (1 shared connections)
- [Doctor Self-Check Command](Doctor_Self-Check_Command.md) (1 shared connections)

## Source Files

- `cli/gherkai_cli/__main__.py`
- `cli/gherkai_cli/deploy.py`

## Audit Trail

- EXTRACTED: 42 (93%)
- INFERRED: 3 (7%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*