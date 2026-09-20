# Deploy Provider Resolution

> 15 nodes · cohesion 0.14

## Key Concepts

- **resolve_provider()** (7 connections) — `cli/gherkai_cli/deploy.py`
- **_cmd_deploy()** (6 connections) — `cli/gherkai_cli/__main__.py`
- **_deploy_provider()** (6 connections) — `cli/gherkai_cli/__main__.py`
- **provider_entry_points()** (5 connections) — `cli/gherkai_cli/deploy.py`
- **_doctor_provider()** (5 connections) — `cli/gherkai_cli/__main__.py`
- **_cmd_destroy()** (4 connections) — `cli/gherkai_cli/__main__.py`
- **_peek_deploy_provider()** (4 connections) — `cli/gherkai_cli/__main__.py`
- **已装的 provider entry point（按名排序、**不加载**）——零个/一个/多个的分叉全据此判。** (1 connections) — `cli/gherkai_cli/deploy.py`
- **按 `--provider` 值（或唯一性）选出 provider 并加载 → `(provider, None)`；失败 → `(None,…** (1 connections) — `cli/gherkai_cli/deploy.py`
- **取已解析的 provider（`main` 窥 argv 时解析、经 `set_defaults` 落在 args 上）。 两个 None…** (1 connections) — `cli/gherkai_cli/__main__.py`
- **[部署方] 分派给 provider（ADR 0037 决策 6）：三个「不真部署」动作互斥，其余走真部署。前端零 IaC 知识。 退出码即 provider…** (1 connections) — `cli/gherkai_cli/__main__.py`
- **[部署方] 拆栈：分派给 provider（哪些资源 RETAIN 是 IaC 侧的事，ADR 0033）。** (1 connections) — `cli/gherkai_cli/__main__.py`
- **从 argv 窥出「是不是 deploy/destroy、有没有 --provider」，据此解析部署 provider（ADR 0037 决策 6）。…** (1 connections) — `cli/gherkai_cli/__main__.py`
- **doctor 的 provider 段：按 entry point 结构化判「没装 / 装了多个 / 装了但坏 / 装了且可自检」，别靠匹配错误文案。…** (1 connections) — `cli/gherkai_cli/__main__.py`
- **EntryPoint** (1 connections)

## Relationships

- [CLI Command Dispatch](CLI_Command_Dispatch.md) (8 shared connections)
- [CLI Plan Command Behavior](CLI_Plan_Command_Behavior.md) (3 shared connections)
- [Run & Submit Commands](Run_%26_Submit_Commands.md) (2 shared connections)
- [Deploy Command Frontend](Deploy_Command_Frontend.md) (1 shared connections)
- [Provider Deploy Subverbs](Provider_Deploy_Subverbs.md) (1 shared connections)

## Source Files

- `cli/gherkai_cli/__main__.py`
- `cli/gherkai_cli/deploy.py`

## Audit Trail

- EXTRACTED: 30 (100%)
- INFERRED: 0 (0%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*