# Event Progress Formatting

> 45 nodes · cohesion 0.11

## Key Concepts

- **StepDone** (48 connections) — `core/gherkai_core/model.py`
- **ScopeDone** (40 connections) — `core/gherkai_core/model.py`
- **wire.py** (36 connections) — `core/gherkai_core/wire.py`
- **ScenarioStarted** (33 connections) — `core/gherkai_core/model.py`
- **ScenarioDone** (32 connections) — `core/gherkai_core/model.py`
- **Votes** (32 connections) — `core/gherkai_core/model.py`
- **_IncClock** (28 connections) — `core/tests/test_schedule.py`
- **_AbortProbeEngine** (18 connections) — `core/tests/test_lifecycle_states.py`
- **StepSkipped** (16 connections) — `core/gherkai_core/model.py`
- **test_abort_then_clean_eof_is_aborted_not_passed()** (15 connections) — `core/tests/test_schedule.py`
- **test_fail_fast_batch_errors()** (14 connections) — `core/tests/test_schedule.py`
- **test_step_skipped_reduced_to_skipped_shortcircuited()** (13 connections) — `core/tests/test_schedule.py`
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
- **test_format_event_step_done_with_votes_and_cost()** (5 connections) — `cli/tests/test_render.py`
- *... and 20 more nodes in this community*

## Relationships

- [Run Scheduling Core](Run_Scheduling_Core.md) (115 shared connections)
- [Event Log & Projection](Event_Log_%26_Projection.md) (47 shared connections)
- [Wire Protocol Serialization](Wire_Protocol_Serialization.md) (21 shared connections)
- [Core Typed Errors](Core_Typed_Errors.md) (13 shared connections)
- [Run State Rendering](Run_State_Rendering.md) (11 shared connections)
- [Run Metadata & S3 Offload](Run_Metadata_%26_S3_Offload.md) (9 shared connections)
- [Local Result Store](Local_Result_Store.md) (7 shared connections)
- [S3 Result Store Port](S3_Result_Store_Port.md) (7 shared connections)
- [Local Report Store](Local_Report_Store.md) (6 shared connections)
- [Explain Rendering Tests](Explain_Rendering_Tests.md) (5 shared connections)
- [Fargate Event Read Tests](Fargate_Event_Read_Tests.md) (4 shared connections)
- [Local & S3 Result Stores](Local_%26_S3_Result_Stores.md) (4 shared connections)

## Source Files

- `cli/gherkai_cli/render.py`
- `cli/tests/test_render.py`
- `core/gherkai_core/model.py`
- `core/gherkai_core/wire.py`
- `core/tests/test_lifecycle_states.py`
- `core/tests/test_schedule.py`

## Audit Trail

- EXTRACTED: 297 (79%)
- INFERRED: 78 (21%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*