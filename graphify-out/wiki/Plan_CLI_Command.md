# Plan CLI Command

> 15 nodes · cohesion 0.13

## Key Concepts

- **_load_and_plan()** (10 connections) — `cli/gherkai_cli/__main__.py`
- **_cmd_plan()** (9 connections) — `cli/gherkai_cli/__main__.py`
- **_resolve_steps_dir()** (7 connections) — `cli/gherkai_cli/__main__.py`
- **_cmd_list_deterministic()** (6 connections) — `cli/gherkai_cli/__main__.py`
- **_probe_deterministic_dispatch()** (4 connections) — `cli/gherkai_cli/__main__.py`
- **_steps_dir_or_error()** (4 connections) — `cli/gherkai_cli/__main__.py`
- **_build_selector()** (3 connections) — `cli/gherkai_cli/__main__.py`
- **_selection_label()** (2 connections) — `cli/gherkai_cli/__main__.py`
- **plan 的派发预期标注（ADR 0036 决策 4）：按引擎分组 step 文本、批量问 worker 命中结果。 返回 {(scope_id,…** (1 connections) — `cli/gherkai_cli/__main__.py`
- **用例预检：读 feature → plan → 渲染 scope/job 分组 + 派发预期标注（ADR 0036）。 **零…** (1 connections) — `cli/gherkai_cli/__main__.py`
- **把 `--scope` / `--tags` / `--scenario` 组装成 `plan(select=…)` 的谓词；都没给 → None（不筛）。…** (1 connections) — `cli/gherkai_cli/__main__.py`
- **`_resolve_steps_dir` 的**不打印**内核：返回 (绝对路径 | None, 错误串 | None)。doctor 把错误串放进机读…** (1 connections) — `cli/gherkai_cli/__main__.py`
- **解析使用方确定性 step 目录（ADR 0037 决策 4）：`--steps-dir` > env `GHERKAI_STEPS_DIR` > 默认…** (1 connections) — `cli/gherkai_cli/__main__.py`
- **按引擎列出确定性 step 清单（ADR 0036）：spawn worker 自述、CLI 只转述——core/CLI 不持有 pattern 语义（ADR…** (1 connections) — `cli/gherkai_cli/__main__.py`
- **plan 与 run 的共享前置装配：votes 校验 → 读 feature → plan。 成功返回 `Job[]`；任一前置失败返回**退出码…** (1 connections) — `cli/gherkai_cli/__main__.py`

## Relationships

- [CLI Command Handlers](CLI_Command_Handlers.md) (15 shared connections)
- [CLI Entry and Plan](CLI_Entry_and_Plan.md) (2 shared connections)
- [Explain Rendering](Explain_Rendering.md) (2 shared connections)
- [Feature Planning Core](Feature_Planning_Core.md) (2 shared connections)
- [Terminal UI Rendering](Terminal_UI_Rendering.md) (1 shared connections)
- [Gherkin Feature Parsing](Gherkin_Feature_Parsing.md) (1 shared connections)
- [Provider Resolution and Doctor](Provider_Resolution_and_Doctor.md) (1 shared connections)

## Source Files

- `cli/gherkai_cli/__main__.py`

## Audit Trail

- EXTRACTED: 38 (100%)
- INFERRED: 0 (0%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*