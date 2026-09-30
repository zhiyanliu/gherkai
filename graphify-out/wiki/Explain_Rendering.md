# Explain Rendering

> 45 nodes · cohesion 0.07

## Key Concepts

- **render.py** (30 connections) — `cli/gherkai_cli/render.py`
- **_add_step()** (12 connections) — `cli/gherkai_cli/render.py`
- **run_tree()** (11 connections) — `cli/gherkai_cli/render.py`
- **explain_to_dict()** (9 connections) — `cli/gherkai_cli/render.py`
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
- *... and 20 more nodes in this community*

## Relationships

- [Terminal UI Rendering](Terminal_UI_Rendering.md) (14 shared connections)
- [Run Result Aggregation Tree](Run_Result_Aggregation_Tree.md) (8 shared connections)
- [Cloud Store Adapters](Cloud_Store_Adapters.md) (5 shared connections)
- [CLI Command Handlers](CLI_Command_Handlers.md) (5 shared connections)
- [Job Domain Models](Job_Domain_Models.md) (3 shared connections)
- [JSON Contract Guards](JSON_Contract_Guards.md) (3 shared connections)
- [Run State Store](Run_State_Store.md) (3 shared connections)
- [Log Pump and Redaction](Log_Pump_and_Redaction.md) (2 shared connections)
- [Plan CLI Command](Plan_CLI_Command.md) (2 shared connections)
- [CLI Run Command Tests](CLI_Run_Command_Tests.md) (1 shared connections)
- [Event Formatting](Event_Formatting.md) (1 shared connections)
- [Run Status Rendering](Run_Status_Rendering.md) (1 shared connections)

## Source Files

- `cli/gherkai_cli/render.py`
- `cli/tests/test_render.py`
- `runtime/gherkai_runtime/textui.py`

## Audit Trail

- EXTRACTED: 119 (100%)
- INFERRED: 0 (0%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*