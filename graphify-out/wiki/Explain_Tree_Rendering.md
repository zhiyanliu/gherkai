# Explain Tree Rendering

> 39 nodes · cohesion 0.09

## Key Concepts

- **render.py** (30 connections) — `cli/gherkai_cli/render.py`
- **_add_step()** (12 connections) — `cli/gherkai_cli/render.py`
- **run_tree()** (11 connections) — `cli/gherkai_cli/render.py`
- **explain_tree()** (8 connections) — `cli/gherkai_cli/render.py`
- **plan_tree()** (8 connections) — `cli/gherkai_cli/render.py`
- **status_text()** (8 connections) — `runtime/gherkai_runtime/textui.py`
- **styled()** (8 connections) — `runtime/gherkai_runtime/textui.py`
- **_add_act()** (7 connections) — `cli/gherkai_cli/render.py`
- **plan_to_dict()** (6 connections) — `cli/gherkai_cli/render.py`
- **render_explain_text()** (6 connections) — `cli/gherkai_cli/render.py`
- **render_plan_text()** (6 connections) — `cli/gherkai_cli/render.py`
- **_one_line()** (5 connections) — `cli/gherkai_cli/render.py`
- **explain_step_expands()** (4 connections) — `cli/gherkai_cli/render.py`
- **_ref_line()** (4 connections) — `cli/gherkai_cli/render.py`
- **_arg_hint()** (3 connections) — `cli/gherkai_cli/render.py`
- **_cost_bits()** (3 connections) — `cli/gherkai_cli/render.py`
- **_dispatch_hint()** (3 connections) — `cli/gherkai_cli/render.py`
- **_evidence_ref()** (3 connections) — `cli/gherkai_cli/render.py`
- **_ms()** (3 connections) — `cli/gherkai_cli/render.py`
- **Job** (3 connections)
- **_thought_text()** (3 connections) — `cli/gherkai_cli/render.py`
- **渲染：把 ADR 0024 事件流与 RunResult 变成人看的文本 / 机器读的 JSON（cli 表层）。 core…** (1 connections) — `cli/gherkai_cli/render.py`
- **plan 产出的 Job[] → 人读的树形预检视图（job → scenario → step 及派发标注，不实际运行；结构见 plan_tree，ADR…** (1 connections) — `cli/gherkai_cli/render.py`
- **plan 视图的树（`render_plan_text` 的结构）。** (1 connections) — `cli/gherkai_cli/render.py`
- **step 的派发预期标注（ADR 0036）：确定性命中/冲突才标，AI 默认不标（噪声控制）。** (1 connections) — `cli/gherkai_cli/render.py`
- *... and 14 more nodes in this community*

## Relationships

- [Rich Text UI Presentation](Rich_Text_UI_Presentation.md) (13 shared connections)
- [CLI Command Entrypoints](CLI_Command_Entrypoints.md) (5 shared connections)
- [Result Tree Text Rendering](Result_Tree_Text_Rendering.md) (5 shared connections)
- [Result Store Serialization](Result_Store_Serialization.md) (2 shared connections)
- [Explain Dict and Redaction](Explain_Dict_and_Redaction.md) (2 shared connections)
- [Engine Listing and JSON Contract](Engine_Listing_and_JSON_Contract.md) (2 shared connections)
- [Run State Rendering](Run_State_Rendering.md) (2 shared connections)
- [Core Adapters Documentation](Core_Adapters_Documentation.md) (1 shared connections)
- [CLI Run Wiring Tests](CLI_Run_Wiring_Tests.md) (1 shared connections)
- [Worker Log Event Formatting](Worker_Log_Event_Formatting.md) (1 shared connections)
- [Run Definition Domain Model](Run_Definition_Domain_Model.md) (1 shared connections)
- [Deploy Provider Discovery](Deploy_Provider_Discovery.md) (1 shared connections)

## Source Files

- `cli/gherkai_cli/render.py`
- `runtime/gherkai_runtime/textui.py`

## Audit Trail

- EXTRACTED: 99 (100%)
- INFERRED: 0 (0%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*