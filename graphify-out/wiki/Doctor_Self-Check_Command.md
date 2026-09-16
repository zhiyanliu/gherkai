# Doctor Self-Check Command

> 10 nodes · cohesion 0.20

## Key Concepts

- **_cmd_doctor()** (8 connections) — `cli/gherkai_cli/__main__.py`
- **_probe_engines()** (5 connections) — `cli/gherkai_cli/__main__.py`
- **_cmd_list_engines()** (4 connections) — `cli/gherkai_cli/__main__.py`
- **_doctor_cloud()** (4 connections) — `cli/gherkai_cli/__main__.py`
- **_steps_dir_or_error()** (4 connections) — `cli/gherkai_cli/__main__.py`
- **`_resolve_steps_dir` 的**不打印**内核：返回 (绝对路径 | None, 错误串 | None)。doctor 把错误串放进机读…** (1 connections) — `cli/gherkai_cli/__main__.py`
- **两引擎各走一遍定位链（ADR 0037 决策 3）→ 机读行：{engine, available, cmd, cwd, source,…** (1 connections) — `cli/gherkai_cli/__main__.py`
- **列出各引擎 worker 的拉起命令 + 命中的定位链级别（ADR 0037 决策 3 的自省口）；miss 则打安装指引。 **恒退…** (1 connections) — `cli/gherkai_cli/__main__.py`
- **只读自检（ADR 0041 决策四）：一个入口、按组件分组；每项 {section, name, ok, required, detail}。 **退出码只看…** (1 connections) — `cli/gherkai_cli/__main__.py`
- **doctor 的 aws / backend 两段（拆出来只为 `_cmd_doctor` 读得下去）：region → 身份 → 版本 → 资源 → 默认…** (1 connections) — `cli/gherkai_cli/__main__.py`

## Relationships

- [CLI Command Entry Points](CLI_Command_Entry_Points.md) (7 shared connections)
- [CLI Main Flow Tests](CLI_Main_Flow_Tests.md) (2 shared connections)
- [Deploy Command Parsers](Deploy_Command_Parsers.md) (1 shared connections)
- [CLI Parser Construction](CLI_Parser_Construction.md) (1 shared connections)
- [JSON Contract Guards](JSON_Contract_Guards.md) (1 shared connections)

## Source Files

- `cli/gherkai_cli/__main__.py`

## Audit Trail

- EXTRACTED: 21 (100%)
- INFERRED: 0 (0%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*