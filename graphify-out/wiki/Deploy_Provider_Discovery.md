# Deploy Provider Discovery

> 31 nodes · cohesion 0.08

## Key Concepts

- **_cmd_doctor()** (11 connections) — `cli/gherkai_cli/__main__.py`
- **deploy.py** (10 connections) — `cli/gherkai_cli/deploy.py`
- **resolve_provider()** (7 connections) — `cli/gherkai_cli/deploy.py`
- **readonly_flag_conflict()** (6 connections) — `cli/gherkai_cli/deploy.py`
- **_cmd_deploy()** (6 connections) — `cli/gherkai_cli/__main__.py`
- **_deploy_provider()** (6 connections) — `cli/gherkai_cli/__main__.py`
- **_doctor_cloud()** (6 connections) — `cli/gherkai_cli/__main__.py`
- **_doctor_provider()** (6 connections) — `cli/gherkai_cli/__main__.py`
- **provider_entry_points()** (5 connections) — `cli/gherkai_cli/deploy.py`
- **.add()** (5 connections) — `runtime/gherkai_runtime/textui.py`
- **add_parsers()** (4 connections) — `cli/gherkai_cli/deploy.py`
- **_add_provider_flag()** (4 connections) — `cli/gherkai_cli/deploy.py`
- **_cmd_destroy()** (4 connections) — `cli/gherkai_cli/__main__.py`
- **_doctor_worker_grace()** (4 connections) — `cli/gherkai_cli/__main__.py`
- **_peek_deploy_provider()** (4 connections) — `cli/gherkai_cli/__main__.py`
- **ArgumentParser** (1 connections)
- **`gherkai deploy` / `gherkai destroy` 的命令行前端：provider 发现 + 命令面 flag，**不含任何 IaC…** (1 connections) — `cli/gherkai_cli/deploy.py`
- **把 `deploy` / `destroy` 两个子命令贴到主 parser 上；`provider` 已解析则让它贴自己的 flag。 解析结果经…** (1 connections) — `cli/gherkai_cli/deploy.py`
- **`--provider`：只在装了多个 provider 时必给（装一个时省略即用它，ADR 0037 决策 6）。** (1 connections) — `cli/gherkai_cli/deploy.py`
- **已装的 provider entry point（按名排序、**不加载**）——零个/一个/多个的分叉全据此判。** (1 connections) — `cli/gherkai_cli/deploy.py`
- **按 `--provider` 值（或唯一性）选出 provider 并加载 → `(provider, None)`；失败 → `(None,…** (1 connections) — `cli/gherkai_cli/deploy.py`
- **provider 子动词（`_deploy_verb`，worker 镜像族、会真写账户）与 `--diff/--synth-…** (1 connections) — `cli/gherkai_cli/deploy.py`
- **取已解析的 provider（`main` 窥 argv 时解析、经 `set_defaults` 落在 args 上）。 两个 None…** (1 connections) — `cli/gherkai_cli/__main__.py`
- **[部署方] 分派给 provider（ADR 0037 决策 6）：三个「不真部署」动作互斥，其余走真部署。前端零 IaC 知识。 退出码即 provider…** (1 connections) — `cli/gherkai_cli/__main__.py`
- **[部署方] 拆栈：分派给 provider（哪些资源 RETAIN 是 IaC 侧的事，ADR 0033）。** (1 connections) — `cli/gherkai_cli/__main__.py`
- *... and 6 more nodes in this community*

## Relationships

- [CLI Command Entrypoints](CLI_Command_Entrypoints.md) (13 shared connections)
- [Plan Command CLI Tests](Plan_Command_CLI_Tests.md) (4 shared connections)
- [Deploy Command Frontend Tests](Deploy_Command_Frontend_Tests.md) (2 shared connections)
- [Deploy CLI Backend Helpers](Deploy_CLI_Backend_Helpers.md) (2 shared connections)
- [CLI Argument Parser](CLI_Argument_Parser.md) (2 shared connections)
- [Provider Deploy Commands](Provider_Deploy_Commands.md) (2 shared connections)
- [Rich Text UI Presentation](Rich_Text_UI_Presentation.md) (2 shared connections)
- [Package Contributor Docs](Package_Contributor_Docs.md) (1 shared connections)
- [Engine Listing and JSON Contract](Engine_Listing_and_JSON_Contract.md) (1 shared connections)
- [Explain Tree Rendering](Explain_Tree_Rendering.md) (1 shared connections)

## Source Files

- `cli/gherkai_cli/__main__.py`
- `cli/gherkai_cli/deploy.py`
- `runtime/gherkai_runtime/textui.py`

## Audit Trail

- EXTRACTED: 62 (93%)
- INFERRED: 5 (7%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*