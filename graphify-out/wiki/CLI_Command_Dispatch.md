# CLI Command Dispatch

> 36 nodes · cohesion 0.08

## Key Concepts

- **gherkai_cli/__main__.py** (73 connections) — `cli/gherkai_cli/__main__.py`
- **_load_and_plan()** (10 connections) — `cli/gherkai_cli/__main__.py`
- **cli/DEVELOPMENT.md** (9 connections) — `cli/DEVELOPMENT.md`
- **deploy.py** (9 connections) — `cli/gherkai_cli/deploy.py`
- **_cmd_plan()** (9 connections) — `cli/gherkai_cli/__main__.py`
- **_cmd_doctor()** (8 connections) — `cli/gherkai_cli/__main__.py`
- **_dist_version()** (7 connections) — `cli/gherkai_cli/__main__.py`
- **_resolve_steps_dir()** (7 connections) — `cli/gherkai_cli/__main__.py`
- **_validate_max_concurrency()** (6 connections) — `cli/gherkai_cli/__main__.py`
- **_cmd_list_deterministic()** (5 connections) — `cli/gherkai_cli/__main__.py`
- **_probe_engines()** (5 connections) — `cli/gherkai_cli/__main__.py`
- **_submit_local()** (5 connections) — `cli/gherkai_cli/__main__.py`
- **_cmd_list_engines()** (4 connections) — `cli/gherkai_cli/__main__.py`
- **_cmd_reconcile()** (4 connections) — `cli/gherkai_cli/__main__.py`
- **_probe_deterministic_dispatch()** (4 connections) — `cli/gherkai_cli/__main__.py`
- **_steps_dir_or_error()** (4 connections) — `cli/gherkai_cli/__main__.py`
- **_build_selector()** (3 connections) — `cli/gherkai_cli/__main__.py`
- **_cmd_tunnel_watch()** (3 connections) — `cli/gherkai_cli/__main__.py`
- **_selection_label()** (2 connections) — `cli/gherkai_cli/__main__.py`
- **`gherkai deploy` / `gherkai destroy` 的命令行前端：provider 发现 + 命令面 flag，**不含任何 IaC…** (1 connections) — `cli/gherkai_cli/deploy.py`
- **gherkai：执行核心库的命令行前端（ADR 0016）。 前端做四件事：解析参数 → 读 feature（compose）→ 注入引擎 resolver…** (1 connections) — `cli/gherkai_cli/__main__.py`
- **plan 的派发预期标注（ADR 0036 决策 4）：按引擎分组 step 文本、批量问 worker 命中结果。 返回 {(scope_id,…** (1 connections) — `cli/gherkai_cli/__main__.py`
- **用例预检：读 feature → plan → 渲染 scope/job 分组 + 派发预期标注（ADR 0036）。 **零…** (1 connections) — `cli/gherkai_cli/__main__.py`
- **把 `--scope` / `--tags` / `--scenario` 组装成 `plan(select=…)` 的谓词；都没给 → None（不筛）。…** (1 connections) — `cli/gherkai_cli/__main__.py`
- **local submit：create_run（文件）+ 建 events SQLite + setsid fork per-run 进程推进。…** (1 connections) — `cli/gherkai_cli/__main__.py`
- *... and 11 more nodes in this community*

## Relationships

- [Run & Submit Commands](Run_%26_Submit_Commands.md) (24 shared connections)
- [Deploy Provider Resolution](Deploy_Provider_Resolution.md) (8 shared connections)
- [CLI Plan Command Behavior](CLI_Plan_Command_Behavior.md) (8 shared connections)
- [CLI Parser Assembly](CLI_Parser_Assembly.md) (6 shared connections)
- [Doctor & Skill Install](Doctor_%26_Skill_Install.md) (6 shared connections)
- [Explain Command](Explain_Command.md) (6 shared connections)
- [CLI Render Layer](CLI_Render_Layer.md) (4 shared connections)
- [Deploy Command Frontend](Deploy_Command_Frontend.md) (4 shared connections)
- [Status Command](Status_Command.md) (4 shared connections)
- [Agent Skill Install](Agent_Skill_Install.md) (2 shared connections)
- [Run State Rendering](Run_State_Rendering.md) (2 shared connections)
- [Feature File Parsing](Feature_File_Parsing.md) (2 shared connections)

## Source Files

- `cli/DEVELOPMENT.md`
- `cli/gherkai_cli/__main__.py`
- `cli/gherkai_cli/deploy.py`

## Audit Trail

- EXTRACTED: 143 (98%)
- INFERRED: 3 (2%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*