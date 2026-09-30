# CLI Argument Parser

> 14 nodes · cohesion 0.15

## Key Concepts

- **_build_parser()** (12 connections) — `cli/gherkai_cli/__main__.py`
- **_installed_version()** (8 connections) — `cli/gherkai_cli/__main__.py`
- **_cmd_skill_install()** (5 connections) — `cli/gherkai_cli/__main__.py`
- **_add_selection_flags()** (4 connections) — `cli/gherkai_cli/__main__.py`
- **test_run_and_submit_share_one_steps_dir_help_text()** (3 connections) — `cli/tests/test_main.py`
- **_parser_nodes()** (3 connections) — `cli/tests/test_skill.py`
- **ArgumentParser** (2 connections)
- **_tunnel_providers()** (2 connections) — `cli/gherkai_cli/__main__.py`
- **run / plan / submit 共用的筛选 flag（ADR 0041 决策一）。语义写在 help 里，解析在 `_build_selector`。** (1 connections) — `cli/gherkai_cli/__main__.py`
- **建主 parser。`provider`（部署 provider，由 `main` 先窥 argv 解析出来）给了就让它贴自己的 flag。 **为何…** (1 connections) — `cli/gherkai_cli/__main__.py`
- **[使用方] 把包内那份 agent skill 收敛安装到目标目录（行为与判据见 `skill_install` 模块头，ADR 0043 决策三）。…** (1 connections) — `cli/gherkai_cli/__main__.py`
- **给**契约比对**用的版本（skew 三态 / worker variant 解析 / 交 provider 写版本戳，ADR 0037 决策…** (1 connections) — `cli/gherkai_cli/__main__.py`
- **`--steps-dir` 的 help 在 run/submit 两处是同一个常量（曾字节级抄两份）：措辞改一处即两处生效。…** (1 connections) — `cli/tests/test_main.py`
- **子命令路径 → 该 parser 节点上声明的 `--flag` 集。`()` = 主 parser。** (1 connections) — `cli/tests/test_skill.py`

## Relationships

- [CLI Command Entrypoints](CLI_Command_Entrypoints.md) (8 shared connections)
- [Plan Command CLI Tests](Plan_Command_CLI_Tests.md) (3 shared connections)
- [Deploy Provider Discovery](Deploy_Provider_Discovery.md) (2 shared connections)
- [Cloud Backend CLI Tests](Cloud_Backend_CLI_Tests.md) (1 shared connections)
- [Agent Skill Installer](Agent_Skill_Installer.md) (1 shared connections)
- [CLI Run Wiring Tests](CLI_Run_Wiring_Tests.md) (1 shared connections)
- [Skill Docs Guardrail Tests](Skill_Docs_Guardrail_Tests.md) (1 shared connections)

## Source Files

- `cli/gherkai_cli/__main__.py`
- `cli/tests/test_main.py`
- `cli/tests/test_skill.py`

## Audit Trail

- EXTRACTED: 31 (100%)
- INFERRED: 0 (0%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*