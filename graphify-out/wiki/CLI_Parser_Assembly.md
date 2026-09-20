# CLI Parser Assembly

> 13 nodes · cohesion 0.17

## Key Concepts

- **_build_parser()** (12 connections) — `cli/gherkai_cli/__main__.py`
- **add_parsers()** (4 connections) — `cli/gherkai_cli/deploy.py`
- **_add_provider_flag()** (4 connections) — `cli/gherkai_cli/deploy.py`
- **_add_selection_flags()** (4 connections) — `cli/gherkai_cli/__main__.py`
- **test_run_and_submit_share_one_steps_dir_help_text()** (3 connections) — `cli/tests/test_main.py`
- **ArgumentParser** (2 connections)
- **_tunnel_providers()** (2 connections) — `cli/gherkai_cli/__main__.py`
- **ArgumentParser** (1 connections)
- **把 `deploy` / `destroy` 两个子命令贴到主 parser 上；`provider` 已解析则让它贴自己的 flag。 解析结果经…** (1 connections) — `cli/gherkai_cli/deploy.py`
- **`--provider`：只在装了多个 provider 时必给（装一个时省略即用它，ADR 0037 决策 6）。** (1 connections) — `cli/gherkai_cli/deploy.py`
- **run / plan / submit 共用的筛选 flag（ADR 0041 决策一）。语义写在 help 里，解析在 `_build_selector`。** (1 connections) — `cli/gherkai_cli/__main__.py`
- **建主 parser。`provider`（部署 provider，由 `main` 先窥 argv 解析出来）给了就让它贴自己的 flag。 **为何…** (1 connections) — `cli/gherkai_cli/__main__.py`
- **`--steps-dir` 的 help 在 run/submit 两处是同一个常量（曾字节级抄两份）：措辞改一处即两处生效。…** (1 connections) — `cli/tests/test_main.py`

## Relationships

- [CLI Command Dispatch](CLI_Command_Dispatch.md) (6 shared connections)
- [Doctor & Skill Install](Doctor_%26_Skill_Install.md) (1 shared connections)
- [CLI Plan Command Behavior](CLI_Plan_Command_Behavior.md) (1 shared connections)
- [Cloud Backend CLI Tests](Cloud_Backend_CLI_Tests.md) (1 shared connections)
- [Skill Doc Flag Guardrails](Skill_Doc_Flag_Guardrails.md) (1 shared connections)
- [CLI Entry Wiring Tests](CLI_Entry_Wiring_Tests.md) (1 shared connections)

## Source Files

- `cli/gherkai_cli/__main__.py`
- `cli/gherkai_cli/deploy.py`
- `cli/tests/test_main.py`

## Audit Trail

- EXTRACTED: 24 (100%)
- INFERRED: 0 (0%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*