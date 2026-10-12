# Event Progress Formatting

> 9 nodes · cohesion 0.22

## Key Concepts

- **Cost** (10 connections) — `core/gherkai_core/model.py`
- **format_event()** (6 connections) — `cli/gherkai_cli/render.py`
- **test_format_event_step_done_with_votes_and_cost()** (5 connections) — `cli/tests/test_render.py`
- **test_format_event_single_vote_hides_tally()** (4 connections) — `cli/tests/test_render.py`
- **test_format_event_omits_scope_id()** (3 connections) — `cli/tests/test_render.py`
- **_cost_from_json()** (3 connections) — `core/gherkai_core/wire.py`
- **Event** (1 connections)
- **单个 ADR 0024 事件 → 一行进度文本（不含 scope_id——scope 归调用方的 `[core <scope>:event]` 前缀， 见…** (1 connections) — `cli/gherkai_cli/render.py`
- **step 级成本：engine 只报**原生量**，平铺、各 optional（ADR 0024）。 原则：core…** (1 connections) — `core/gherkai_core/model.py`

## Relationships

- [Run Scheduling Events Core](Run_Scheduling_Events_Core.md) (9 shared connections)
- [Cloud Adapter Boundary Modules](Cloud_Adapter_Boundary_Modules.md) (4 shared connections)
- [Result Tree Rendering](Result_Tree_Rendering.md) (3 shared connections)
- [Plan Explain Rendering](Plan_Explain_Rendering.md) (1 shared connections)
- [Event Wire Protocol](Event_Wire_Protocol.md) (1 shared connections)

## Source Files

- `cli/gherkai_cli/render.py`
- `cli/tests/test_render.py`
- `core/gherkai_core/model.py`
- `core/gherkai_core/wire.py`

## Audit Trail

- EXTRACTED: 25 (96%)
- INFERRED: 1 (4%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*