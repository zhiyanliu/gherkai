# Explain Command

> 14 nodes · cohesion 0.16

## Key Concepts

- **_explain_emit()** (11 connections) — `cli/gherkai_cli/__main__.py`
- **explain_to_dict()** (8 connections) — `cli/gherkai_cli/render.py`
- **_cmd_explain()** (6 connections) — `cli/gherkai_cli/__main__.py`
- **_explain_cloud()** (6 connections) — `cli/gherkai_cli/__main__.py`
- **_explain_empty()** (5 connections) — `cli/gherkai_cli/__main__.py`
- **_explain_read_evidence()** (3 connections) — `cli/gherkai_cli/__main__.py`
- **_explain_scenario_matches()** (3 connections) — `cli/gherkai_cli/__main__.py`
- **explain 的 `--scenario` 匹配：id 全等 / 行号 / 标题子串，多个 SEL 之间「或」。 **另起一份、不复用…** (1 connections) — `cli/gherkai_cli/__main__.py`
- **读该 step 的机读证据 → `(evidence | None, evidence_missing | None)`（ADR 0042 决策四）。…** (1 connections) — `cli/gherkai_cli/__main__.py`
- **没有判定明细可渲染时的输出：人读打一行提示、`--json` 仍只打一个（scopes 为空的）文档。恒以退出码 0 结束。 退出码 0 而非 2…** (1 connections) — `cli/gherkai_cli/__main__.py`
- **local/cloud 共用的后半段：取判定明细 → 筛 scenario/step → 合成文档 → 打文本或 JSON。 带 `scope_id` 时只…** (1 connections) — `cli/gherkai_cli/__main__.py`
- **[查询] 看一个 run 的 step 级证据（ADR 0042 决策四）。 local：读 `--report-dir` 下的…** (1 connections) — `cli/gherkai_cli/__main__.py`
- **cloud explain：DDB 读 run 运行态、S3 读判定明细与证据。 次序同…** (1 connections) — `cli/gherkai_cli/__main__.py`
- **把 JobResult 列表 + evidence 合成 explain 的机读文档（形状即 ADR 0042 决策四的 JSON 形态）。 **骨架是…** (1 connections) — `cli/gherkai_cli/render.py`

## Relationships

- [CLI Command Dispatch](CLI_Command_Dispatch.md) (6 shared connections)
- [Run & Submit Commands](Run_%26_Submit_Commands.md) (4 shared connections)
- [CLI Render Layer](CLI_Render_Layer.md) (3 shared connections)
- [CLI Plan Command Behavior](CLI_Plan_Command_Behavior.md) (1 shared connections)
- [Doctor & Skill Install](Doctor_%26_Skill_Install.md) (1 shared connections)
- [Local & S3 Result Stores](Local_%26_S3_Result_Stores.md) (1 shared connections)
- [JSON Field Contract Tests](JSON_Field_Contract_Tests.md) (1 shared connections)
- [Explain Rendering Tests](Explain_Rendering_Tests.md) (1 shared connections)
- [S3 Result Store Port](S3_Result_Store_Port.md) (1 shared connections)

## Source Files

- `cli/gherkai_cli/__main__.py`
- `cli/gherkai_cli/render.py`

## Audit Trail

- EXTRACTED: 34 (100%)
- INFERRED: 0 (0%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*