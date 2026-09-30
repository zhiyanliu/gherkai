# CLI Parser Construction

> 14 nodes · cohesion 0.15

## Key Concepts

- **_build_parser()** (12 connections) — `cli/gherkai_cli/__main__.py`
- **_dist_version()** (7 connections) — `cli/gherkai_cli/__main__.py`
- **_add_selection_flags()** (4 connections) — `cli/gherkai_cli/__main__.py`
- **_runtime_version()** (4 connections) — `runtime/gherkai_runtime/compose.py`
- **test_run_and_submit_share_one_steps_dir_help_text()** (3 connections) — `cli/tests/test_main.py`
- **_parser_nodes()** (3 connections) — `cli/tests/test_skill.py`
- **ArgumentParser** (2 connections)
- **_tunnel_providers()** (2 connections) — `cli/gherkai_cli/__main__.py`
- **run / plan / submit 共用的筛选 flag（ADR 0041 决策一）。语义写在 help 里，解析在 `_build_selector`。** (1 connections) — `cli/gherkai_cli/__main__.py`
- **建主 parser。`provider`（部署 provider，由 `main` 先窥 argv 解析出来）给了就让它贴自己的 flag。 **为何…** (1 connections) — `cli/gherkai_cli/__main__.py`
- **发行版本字符串（唯一真源是 git tag，经 uv-dynamic-versioning 写进包元数据，ADR 0037 决策 2b；…** (1 connections) — `cli/gherkai_cli/__main__.py`
- **`--steps-dir` 的 help 在 run/submit 两处是同一个常量（曾字节级抄两份）：措辞改一处即两处生效。…** (1 connections) — `cli/tests/test_main.py`
- **子命令路径 → 该 parser 节点上声明的 `--flag` 集。`()` = 主 parser。** (1 connections) — `cli/tests/test_skill.py`
- **本包（`gherkai-runtime`）的发行版本：定位链第四级的 pin 值。未装成包（从源码直接运行）→ None。** (1 connections) — `runtime/gherkai_runtime/compose.py`

## Relationships

- [CLI Command Handlers](CLI_Command_Handlers.md) (6 shared connections)
- [Deploy Command Frontend](Deploy_Command_Frontend.md) (1 shared connections)
- [CLI Entry and Plan](CLI_Entry_and_Plan.md) (1 shared connections)
- [Cloud Backend CLI Tests](Cloud_Backend_CLI_Tests.md) (1 shared connections)
- [Provider Resolution and Doctor](Provider_Resolution_and_Doctor.md) (1 shared connections)
- [Deploy Command Frontend Tests](Deploy_Command_Frontend_Tests.md) (1 shared connections)
- [CLI Run Command Tests](CLI_Run_Command_Tests.md) (1 shared connections)
- [Agent Skill Doc Guards](Agent_Skill_Doc_Guards.md) (1 shared connections)
- [Cloud Resource Resolution](Cloud_Resource_Resolution.md) (1 shared connections)
- [SSM Path Naming](SSM_Path_Naming.md) (1 shared connections)

## Source Files

- `cli/gherkai_cli/__main__.py`
- `cli/tests/test_main.py`
- `cli/tests/test_skill.py`
- `runtime/gherkai_runtime/compose.py`

## Audit Trail

- EXTRACTED: 28 (97%)
- INFERRED: 1 (3%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*