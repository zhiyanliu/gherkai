# Deploy/Destroy CLI Commands

> 6 nodes · cohesion 0.33

## Key Concepts

- **_deploy_provider()** (6 connections) — `cli/gherkai_cli/__main__.py`
- **_cmd_deploy()** (4 connections) — `cli/gherkai_cli/__main__.py`
- **_cmd_destroy()** (4 connections) — `cli/gherkai_cli/__main__.py`
- **取已解析的 provider（`main` 窥 argv 时解析、经 `set_defaults` 落在 args 上）。 两个 None…** (1 connections) — `cli/gherkai_cli/__main__.py`
- **[部署方] 分派给 provider（ADR 0037 决策 6）：三个「不真部署」动作互斥，其余走真部署。皮零 IaC 知识。 退出码即 provider…** (1 connections) — `cli/gherkai_cli/__main__.py`
- **[部署方] 拆栈：分派给 provider（哪些资源 RETAIN 是 IaC 侧的事，ADR 0033）。** (1 connections) — `cli/gherkai_cli/__main__.py`

## Relationships

- [CLI Main Entry](CLI_Main_Entry.md) (3 shared connections)
- [CLI Run Entry Tests](CLI_Run_Entry_Tests.md) (2 shared connections)
- [Deploy Provider Discovery](Deploy_Provider_Discovery.md) (1 shared connections)
- [CLI Run/Submit Commands](CLI_Run-Submit_Commands.md) (1 shared connections)

## Source Files

- `cli/gherkai_cli/__main__.py`

## Audit Trail

- EXTRACTED: 12 (100%)
- INFERRED: 0 (0%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*