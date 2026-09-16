# Explain Rendering

> 40 nodes · cohesion 0.07

## Key Concepts

- **render.py** (25 connections) — `cli/gherkai_cli/render.py`
- **_explain_emit()** (11 connections) — `cli/gherkai_cli/__main__.py`
- **_step_lines()** (9 connections) — `cli/gherkai_cli/render.py`
- **explain_to_dict()** (8 connections) — `cli/gherkai_cli/render.py`
- **plan_to_dict()** (6 connections) — `cli/gherkai_cli/render.py`
- **render_explain_text()** (6 connections) — `cli/gherkai_cli/render.py`
- **render_plan_text()** (6 connections) — `cli/gherkai_cli/render.py`
- **_explain_empty()** (5 connections) — `cli/gherkai_cli/__main__.py`
- **_act_lines()** (5 connections) — `cli/gherkai_cli/render.py`
- **_one_line()** (5 connections) — `cli/gherkai_cli/render.py`
- **explain_step_expands()** (4 connections) — `cli/gherkai_cli/render.py`
- **_ref_line()** (4 connections) — `cli/gherkai_cli/render.py`
- **_explain_read_evidence()** (3 connections) — `cli/gherkai_cli/__main__.py`
- **_explain_scenario_matches()** (3 connections) — `cli/gherkai_cli/__main__.py`
- **_arg_hint()** (3 connections) — `cli/gherkai_cli/render.py`
- **_cost_bits()** (3 connections) — `cli/gherkai_cli/render.py`
- **_dispatch_hint()** (3 connections) — `cli/gherkai_cli/render.py`
- **_evidence_ref()** (3 connections) — `cli/gherkai_cli/render.py`
- **_ms()** (3 connections) — `cli/gherkai_cli/render.py`
- **_thought_lines()** (3 connections) — `cli/gherkai_cli/render.py`
- **Job** (2 connections)
- **explain 的 `--scenario` 匹配：id 全等 / 行号 / 标题子串，多个 SEL 之间「或」。 **另起一份、不复用…** (1 connections) — `cli/gherkai_cli/__main__.py`
- **读该 step 的机读证据 → `(evidence | None, evidence_missing | None)`（ADR 0042 决策四）。…** (1 connections) — `cli/gherkai_cli/__main__.py`
- **没有判定明细可渲染时的输出：人读打一行提示、`--json` 仍只打一个（scopes 为空的）文档。恒退 0。 退 0 而非 2 是刻意的（ADR 0042…** (1 connections) — `cli/gherkai_cli/__main__.py`
- **local/cloud 共用的后半段：取判定明细 → 筛 scenario/step → 合成文档 → 打文本或 JSON。 带 `scope_id` 时只…** (1 connections) — `cli/gherkai_cli/__main__.py`
- *... and 15 more nodes in this community*

## Relationships

- [CLI Command Entry Points](CLI_Command_Entry_Points.md) (11 shared connections)
- [Text Render & Wording Guards](Text_Render_%26_Wording_Guards.md) (5 shared connections)
- [DynamoDB RunStore Adapter](DynamoDB_RunStore_Adapter.md) (3 shared connections)
- [JSON Contract Guards](JSON_Contract_Guards.md) (3 shared connections)
- [Job Explain & S3 Offload](Job_Explain_%26_S3_Offload.md) (2 shared connections)
- [Cloud Boto3 Guards & EventLog](Cloud_Boto3_Guards_%26_EventLog.md) (1 shared connections)
- [CLI Run Command Tests](CLI_Run_Command_Tests.md) (1 shared connections)
- [Run State Rendering](Run_State_Rendering.md) (1 shared connections)
- [Event Formatting](Event_Formatting.md) (1 shared connections)
- [S3 Result Store](S3_Result_Store.md) (1 shared connections)

## Source Files

- `cli/gherkai_cli/__main__.py`
- `cli/gherkai_cli/render.py`

## Audit Trail

- EXTRACTED: 84 (100%)
- INFERRED: 0 (0%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*