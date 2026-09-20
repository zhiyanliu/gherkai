# Doctor & Skill Install

> 10 nodes · cohesion 0.20

## Key Concepts

- **_cloud_skew_gate()** (8 connections) — `cli/gherkai_cli/__main__.py`
- **_installed_version()** (8 connections) — `cli/gherkai_cli/__main__.py`
- **_cmd_skill_install()** (5 connections) — `cli/gherkai_cli/__main__.py`
- **_doctor_cloud()** (5 connections) — `cli/gherkai_cli/__main__.py`
- **_doctor_worker_grace()** (3 connections) — `cli/gherkai_cli/__main__.py`
- **cloud 路径的**第一道闸**：CLI 与后端的版本 skew 三态（ADR 0037 决策 7）。 返回 `(退出码 or None, 后端版本戳 or…** (1 connections) — `cli/gherkai_cli/__main__.py`
- **[使用方] 把包内那份 agent skill 收敛安装到目标目录（行为与判据见 `skill_install` 模块头，ADR 0043 决策三）。…** (1 connections) — `cli/gherkai_cli/__main__.py`
- **给**契约比对**用的版本（skew 三态 / worker variant 解析 / 交 provider 写版本戳，ADR 0037 决策…** (1 connections) — `cli/gherkai_cli/__main__.py`
- **doctor 的 aws / backend 两段（拆出来只为 `_cmd_doctor` 读得下去）：region → 身份 → 版本 → 资源 → 默认…** (1 connections) — `cli/gherkai_cli/__main__.py`
- **doctor 的 `backend.worker.grace` 行：引擎 worker 自报的最短收尾宽限 vs 云端 task-def 的停止宽限。…** (1 connections) — `cli/gherkai_cli/__main__.py`

## Relationships

- [CLI Command Dispatch](CLI_Command_Dispatch.md) (6 shared connections)
- [Run & Submit Commands](Run_%26_Submit_Commands.md) (4 shared connections)
- [CLI Plan Command Behavior](CLI_Plan_Command_Behavior.md) (2 shared connections)
- [Explain Command](Explain_Command.md) (1 shared connections)
- [Status Command](Status_Command.md) (1 shared connections)
- [Agent Skill Install](Agent_Skill_Install.md) (1 shared connections)
- [CLI Parser Assembly](CLI_Parser_Assembly.md) (1 shared connections)

## Source Files

- `cli/gherkai_cli/__main__.py`

## Audit Trail

- EXTRACTED: 25 (100%)
- INFERRED: 0 (0%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*