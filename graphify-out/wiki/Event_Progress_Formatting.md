# Event Progress Formatting

> 40 nodes · cohesion 0.12

## Key Concepts

- **StepDone** (48 connections) — `core/gherkai_core/model.py`
- **ScopeDone** (40 connections) — `core/gherkai_core/model.py`
- **ScenarioStarted** (33 connections) — `core/gherkai_core/model.py`
- **ScenarioDone** (32 connections) — `core/gherkai_core/model.py`
- **Votes** (32 connections) — `core/gherkai_core/model.py`
- **_IncClock** (28 connections) — `core/tests/test_schedule.py`
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
- **test_format_event_single_vote_hides_tally()** (4 connections) — `cli/tests/test_render.py`
- **._gen()** (4 connections) — `core/tests/test_lifecycle_states.py`
- *... and 15 more nodes in this community*

## Relationships

- [Schedule Module Tests](Schedule_Module_Tests.md) (110 shared connections)
- [Cloud Launcher & Fargate Adapters](Cloud_Launcher_%26_Fargate_Adapters.md) (32 shared connections)
- [Fake DDB Table & SQLite Records](Fake_DDB_Table_%26_SQLite_Records.md) (28 shared connections)
- [Job/Scenario Explain Model](Job-Scenario_Explain_Model.md) (18 shared connections)
- [Wire Protocol Serialization](Wire_Protocol_Serialization.md) (12 shared connections)
- [Severity Aggregation & Fake Engine](Severity_Aggregation_%26_Fake_Engine.md) (11 shared connections)
- [Local Result Store & Persistence](Local_Result_Store_%26_Persistence.md) (7 shared connections)
- [Result Rendering & Explain](Result_Rendering_%26_Explain.md) (5 shared connections)
- [Local Report Store](Local_Report_Store.md) (5 shared connections)
- [Fargate Engine Adapter Tests](Fargate_Engine_Adapter_Tests.md) (2 shared connections)
- [Event Read Gap Handling](Event_Read_Gap_Handling.md) (2 shared connections)
- [Job State Serialization](Job_State_Serialization.md) (2 shared connections)

## Source Files

- `cli/gherkai_cli/render.py`
- `cli/tests/test_render.py`
- `core/gherkai_core/model.py`
- `core/gherkai_core/wire.py`
- `core/tests/test_lifecycle_states.py`
- `core/tests/test_schedule.py`

## Audit Trail

- EXTRACTED: 264 (80%)
- INFERRED: 68 (20%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*