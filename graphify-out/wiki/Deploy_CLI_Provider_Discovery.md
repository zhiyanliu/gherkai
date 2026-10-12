# Deploy CLI Provider Discovery

> 33 nodes · cohesion 0.08

## Key Concepts

- **_build_parser()** (12 connections) — `cli/gherkai_cli/__main__.py`
- **_cmd_doctor()** (11 connections) — `cli/gherkai_cli/__main__.py`
- **deploy.py** (8 connections) — `cli/gherkai_cli/deploy.py`
- **resolve_provider()** (7 connections) — `cli/gherkai_cli/deploy.py`
- **_dist_version()** (7 connections) — `cli/gherkai_cli/__main__.py`
- **_doctor_cloud()** (6 connections) — `cli/gherkai_cli/__main__.py`
- **_doctor_provider()** (6 connections) — `cli/gherkai_cli/__main__.py`
- **provider_entry_points()** (5 connections) — `cli/gherkai_cli/deploy.py`
- **.add()** (5 connections) — `runtime/gherkai_runtime/textui.py`
- **add_parsers()** (4 connections) — `cli/gherkai_cli/deploy.py`
- **_add_provider_flag()** (4 connections) — `cli/gherkai_cli/deploy.py`
- **_add_selection_flags()** (4 connections) — `cli/gherkai_cli/__main__.py`
- **_doctor_worker_grace()** (4 connections) — `cli/gherkai_cli/__main__.py`
- **_peek_deploy_provider()** (4 connections) — `cli/gherkai_cli/__main__.py`
- **test_run_and_submit_share_one_steps_dir_help_text()** (3 connections) — `cli/tests/test_main.py`
- **ArgumentParser** (2 connections)
- **_tunnel_providers()** (2 connections) — `cli/gherkai_cli/__main__.py`
- **ArgumentParser** (1 connections)
- **`gherkai deploy` / `gherkai destroy` 的命令行前端：provider 发现 + 命令面 flag，**不含任何 IaC…** (1 connections) — `cli/gherkai_cli/deploy.py`
- **把 `deploy` / `destroy` 两个子命令贴到主 parser 上；`provider` 已解析则让它贴自己的 flag。 解析结果经…** (1 connections) — `cli/gherkai_cli/deploy.py`
- **`--provider`：只在装了多个 provider 时必给（装一个时省略即用它，ADR 0037 决策 6）。** (1 connections) — `cli/gherkai_cli/deploy.py`
- **已装的 provider entry point（按名排序、**不加载**）——零个/一个/多个的分叉全据此判。** (1 connections) — `cli/gherkai_cli/deploy.py`
- **按 `--provider` 值（或唯一性）选出 provider 并加载 → `(provider, None)`；失败 → `(None,…** (1 connections) — `cli/gherkai_cli/deploy.py`
- **run / plan / submit 共用的筛选 flag（ADR 0041 决策一）。语义写在 help 里，解析在 `_build_selector`。** (1 connections) — `cli/gherkai_cli/__main__.py`
- **建主 parser。`provider`（部署 provider，由 `main` 先窥 argv 解析出来）给了就让它贴自己的 flag。 **为何…** (1 connections) — `cli/gherkai_cli/__main__.py`
- *... and 8 more nodes in this community*

## Relationships

- [CLI Command Dispatch Entry](CLI_Command_Dispatch_Entry.md) (15 shared connections)
- [Deploy Command Frontend Tests](Deploy_Command_Frontend_Tests.md) (3 shared connections)
- [CLI Plan Command Behavior](CLI_Plan_Command_Behavior.md) (3 shared connections)
- [Human-Readable Text UI](Human-Readable_Text_UI.md) (2 shared connections)
- [CDK Command Execution](CDK_Command_Execution.md) (1 shared connections)
- [Cloud Backend CLI Wiring Tests](Cloud_Backend_CLI_Wiring_Tests.md) (1 shared connections)
- [Skill CLI Command Linting](Skill_CLI_Command_Linting.md) (1 shared connections)
- [CLI JSON Contract Tests](CLI_JSON_Contract_Tests.md) (1 shared connections)
- [Plan & Explain Rendering](Plan_%26_Explain_Rendering.md) (1 shared connections)
- [Worker Command Resolution Chain](Worker_Command_Resolution_Chain.md) (1 shared connections)
- [CLI Run Entry Tests](CLI_Run_Entry_Tests.md) (1 shared connections)

## Source Files

- `cli/gherkai_cli/__main__.py`
- `cli/gherkai_cli/deploy.py`
- `cli/tests/test_main.py`
- `runtime/gherkai_runtime/textui.py`

## Audit Trail

- EXTRACTED: 68 (97%)
- INFERRED: 2 (3%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*