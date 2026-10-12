# Plan & Explain Rendering

> 41 nodes · cohesion 0.08

## Key Concepts

- **render.py** (30 connections) — `cli/gherkai_cli/render.py`
- **_add_step()** (12 connections) — `cli/gherkai_cli/render.py`
- **run_tree()** (11 connections) — `cli/gherkai_cli/render.py`
- **explain_tree()** (8 connections) — `cli/gherkai_cli/render.py`
- **plan_tree()** (8 connections) — `cli/gherkai_cli/render.py`
- **render_run_state()** (8 connections) — `cli/gherkai_cli/render.py`
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
- **`status` 的 RunState 人读渲染（轻量；权威判定明细读 jobs/*.json 或 --json）。 local/cloud…** (1 connections) — `cli/gherkai_cli/render.py`
- **plan 产出的 Job[] → 人读的树形预检视图（job → scenario → step 及派发标注，不实际运行；结构见 plan_tree，ADR…** (1 connections) — `cli/gherkai_cli/render.py`
- *... and 16 more nodes in this community*

## Relationships

- [Human-Readable Text UI](Human-Readable_Text_UI.md) (14 shared connections)
- [CLI Command Dispatch Entry](CLI_Command_Dispatch_Entry.md) (6 shared connections)
- [Result Rendering & Explain](Result_Rendering_%26_Explain.md) (5 shared connections)
- [Run State Rendering & DDB Store](Run_State_Rendering_%26_DDB_Store.md) (3 shared connections)
- [S3 Result Store](S3_Result_Store.md) (2 shared connections)
- [Explain JSON & Redaction](Explain_JSON_%26_Redaction.md) (2 shared connections)
- [CLI JSON Contract Tests](CLI_JSON_Contract_Tests.md) (2 shared connections)
- [Cloud Launcher & Fargate Adapters](Cloud_Launcher_%26_Fargate_Adapters.md) (1 shared connections)
- [CLI Run Entry Tests](CLI_Run_Entry_Tests.md) (1 shared connections)
- [Event Progress Formatting](Event_Progress_Formatting.md) (1 shared connections)
- [Job/Scenario Explain Model](Job-Scenario_Explain_Model.md) (1 shared connections)
- [Deploy CLI Provider Discovery](Deploy_CLI_Provider_Discovery.md) (1 shared connections)

## Source Files

- `cli/gherkai_cli/render.py`
- `runtime/gherkai_runtime/textui.py`

## Audit Trail

- EXTRACTED: 105 (100%)
- INFERRED: 0 (0%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*