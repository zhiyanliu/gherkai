# Event Progress Formatting

> 62 nodes · cohesion 0.07

## Key Concepts

- **StepDone** (43 connections) — `core/gherkai_core/model.py`
- **ScopeDone** (36 connections) — `core/gherkai_core/model.py`
- **test_wire.py** (35 connections) — `core/tests/test_wire.py`
- **ScenarioStarted** (32 connections) — `core/gherkai_core/model.py`
- **ScenarioDone** (30 connections) — `core/gherkai_core/model.py`
- **Votes** (30 connections) — `core/gherkai_core/model.py`
- **_IncClock** (28 connections) — `core/tests/test_schedule.py`
- **event_from_json()** (27 connections) — `core/gherkai_core/wire.py`
- **Action** (21 connections) — `core/gherkai_core/project.py`
- **StepSkipped** (15 connections) — `core/gherkai_core/model.py`
- **test_abort_then_clean_eof_is_aborted_not_passed()** (15 connections) — `core/tests/test_schedule.py`
- **test_step_skipped_reduced_to_skipped_shortcircuited()** (13 connections) — `core/tests/test_schedule.py`
- **StepStarted** (12 connections) — `core/gherkai_core/model.py`
- **test_failed_and_error_steps_cost_still_aggregated()** (12 connections) — `core/tests/test_schedule.py`
- **test_partial_completion_without_scope_done_not_passed()** (12 connections) — `core/tests/test_schedule.py`
- **test_scope_report_refs_reduced()** (12 connections) — `core/tests/test_schedule.py`
- **test_step_report_refs_reduced()** (12 connections) — `core/tests/test_schedule.py`
- **test_step_skipped_does_not_pollute_scenario_or_run_status()** (12 connections) — `core/tests/test_schedule.py`
- **test_step_skipped_without_scenario_done_still_recorded()** (12 connections) — `core/tests/test_schedule.py`
- **Cost** (10 connections) — `core/gherkai_core/model.py`
- **_full_timed_events()** (9 connections) — `core/tests/test_schedule.py`
- **_events_with_time()** (8 connections) — `core/tests/test_schedule.py`
- **_events_with_tokens()** (8 connections) — `core/tests/test_schedule.py`
- **_failing_events()** (8 connections) — `core/tests/test_schedule.py`
- **format_event()** (6 connections) — `cli/gherkai_cli/render.py`
- *... and 37 more nodes in this community*

## Relationships

- [Run Scheduling Engine](Run_Scheduling_Engine.md) (107 shared connections)
- [Run Result Rendering](Run_Result_Rendering.md) (44 shared connections)
- [Engine Ports & Adapters](Engine_Ports_%26_Adapters.md) (33 shared connections)
- [Terminal Status Aggregation](Terminal_Status_Aggregation.md) (12 shared connections)
- [State Projection & Planning](State_Projection_%26_Planning.md) (11 shared connections)
- [Report Refs & Results](Report_Refs_%26_Results.md) (8 shared connections)
- [Local Result Store](Local_Result_Store.md) (7 shared connections)
- [Run State Rendering](Run_State_Rendering.md) (4 shared connections)
- [Boto Guard & S3 Offload](Boto_Guard_%26_S3_Offload.md) (4 shared connections)
- [Fargate Worker Handle](Fargate_Worker_Handle.md) (3 shared connections)
- [Worker Exit Code Mapping](Worker_Exit_Code_Mapping.md) (3 shared connections)
- [Fargate Engine Tests](Fargate_Engine_Tests.md) (2 shared connections)

## Source Files

- `cli/gherkai_cli/render.py`
- `cli/tests/test_render.py`
- `core/gherkai_core/model.py`
- `core/gherkai_core/project.py`
- `core/gherkai_core/wire.py`
- `core/tests/test_lifecycle_states.py`
- `core/tests/test_schedule.py`
- `core/tests/test_wire.py`

## Audit Trail

- EXTRACTED: 313 (81%)
- INFERRED: 74 (19%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*