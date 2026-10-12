# Plan Explain Rendering

> 43 nodes · cohesion 0.08

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
- **test_render_run_state_lists_jobs_and_session_lineage()** (4 connections) — `cli/tests/test_render.py`
- **test_render_run_state_shows_ended_at_when_terminal()** (4 connections) — `cli/tests/test_render.py`
- **_arg_hint()** (3 connections) — `cli/gherkai_cli/render.py`
- **_cost_bits()** (3 connections) — `cli/gherkai_cli/render.py`
- **_dispatch_hint()** (3 connections) — `cli/gherkai_cli/render.py`
- **_evidence_ref()** (3 connections) — `cli/gherkai_cli/render.py`
- **_ms()** (3 connections) — `cli/gherkai_cli/render.py`
- **Job** (3 connections)
- **_thought_text()** (3 connections) — `cli/gherkai_cli/render.py`
- **渲染：把 ADR 0024 事件流与 RunResult 变成人看的文本 / 机器读的 JSON（cli 表层）。 core…** (1 connections) — `cli/gherkai_cli/render.py`
- *... and 18 more nodes in this community*

## Relationships

- [Text UI Rendering](Text_UI_Rendering.md) (14 shared connections)
- [Result Tree Rendering](Result_Tree_Rendering.md) (6 shared connections)
- [CLI Command Entry Points](CLI_Command_Entry_Points.md) (4 shared connections)
- [Explain Output Rendering](Explain_Output_Rendering.md) (3 shared connections)
- [Run State Store](Run_State_Store.md) (3 shared connections)
- [Result Store Adapters](Result_Store_Adapters.md) (2 shared connections)
- [Engine Listing JSON Contract](Engine_Listing_JSON_Contract.md) (2 shared connections)
- [DynamoDB Job State Store](DynamoDB_Job_State_Store.md) (2 shared connections)
- [Cloud Adapter Boundary Modules](Cloud_Adapter_Boundary_Modules.md) (1 shared connections)
- [Subprocess Engine Adapter](Subprocess_Engine_Adapter.md) (1 shared connections)
- [CLI Run Entry Tests](CLI_Run_Entry_Tests.md) (1 shared connections)
- [Event Progress Formatting](Event_Progress_Formatting.md) (1 shared connections)

## Source Files

- `cli/gherkai_cli/render.py`
- `cli/tests/test_render.py`
- `runtime/gherkai_runtime/textui.py`

## Audit Trail

- EXTRACTED: 111 (100%)
- INFERRED: 0 (0%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*