# Event Formatting & Cost Model

> 38 nodes · cohesion 0.13

## Key Concepts

- **StepDone** (43 connections) — `core/gherkai_core/model.py`
- **ScopeDone** (36 connections) — `core/gherkai_core/model.py`
- **ScenarioStarted** (32 connections) — `core/gherkai_core/model.py`
- **ScenarioDone** (30 connections) — `core/gherkai_core/model.py`
- **Votes** (30 connections) — `core/gherkai_core/model.py`
- **_IncClock** (28 connections) — `core/tests/test_schedule.py`
- **test_abort_then_clean_eof_is_aborted_not_passed()** (15 connections) — `core/tests/test_schedule.py`
- **test_fail_fast_batch_errors()** (14 connections) — `core/tests/test_schedule.py`
- **test_step_skipped_reduced_to_skipped_shortcircuited()** (13 connections) — `core/tests/test_schedule.py`
- **test_failed_and_error_steps_cost_still_aggregated()** (12 connections) — `core/tests/test_schedule.py`
- **test_partial_completion_without_scope_done_not_passed()** (12 connections) — `core/tests/test_schedule.py`
- **test_scope_report_refs_reduced()** (12 connections) — `core/tests/test_schedule.py`
- **test_step_report_refs_reduced()** (12 connections) — `core/tests/test_schedule.py`
- **test_step_skipped_does_not_pollute_scenario_or_run_status()** (12 connections) — `core/tests/test_schedule.py`
- **test_step_skipped_without_scenario_done_still_recorded()** (12 connections) — `core/tests/test_schedule.py`
- **test_timeout_with_fake_clock()** (12 connections) — `core/tests/test_schedule.py`
- **Cost** (10 connections) — `core/gherkai_core/model.py`
- **_full_timed_events()** (9 connections) — `core/tests/test_schedule.py`
- **_events_with_time()** (8 connections) — `core/tests/test_schedule.py`
- **_events_with_tokens()** (8 connections) — `core/tests/test_schedule.py`
- **_failing_events()** (8 connections) — `core/tests/test_schedule.py`
- **format_event()** (6 connections) — `cli/gherkai_cli/render.py`
- **test_format_event_step_done_with_votes_and_cost()** (5 connections) — `cli/tests/test_render.py`
- **test_format_event_single_vote_hides_tally()** (4 connections) — `cli/tests/test_render.py`
- **._gen()** (4 connections) — `core/tests/test_lifecycle_states.py`
- *... and 13 more nodes in this community*

## Relationships

- [Run Schedule Orchestration](Run_Schedule_Orchestration.md) (113 shared connections)
- [SQLite Event Log & Projection](SQLite_Event_Log_%26_Projection.md) (33 shared connections)
- [Engine Ports & Adapters](Engine_Ports_%26_Adapters.md) (20 shared connections)
- [Terminal Status Aggregation](Terminal_Status_Aggregation.md) (11 shared connections)
- [Wire Protocol Serialization](Wire_Protocol_Serialization.md) (10 shared connections)
- [Render & ReportStore Local](Render_%26_ReportStore_Local.md) (9 shared connections)
- [Run Result Verdict Model](Run_Result_Verdict_Model.md) (7 shared connections)
- [Run Persistence Orchestration](Run_Persistence_Orchestration.md) (6 shared connections)
- [Fargate Engine Unit Tests](Fargate_Engine_Unit_Tests.md) (2 shared connections)
- [Fargate Engine Adapter](Fargate_Engine_Adapter.md) (2 shared connections)
- [DynamoDB RunStore Conditional Writes](DynamoDB_RunStore_Conditional_Writes.md) (2 shared connections)
- [ResultStore Local/S3](ResultStore_Local-S3.md) (2 shared connections)

## Source Files

- `cli/gherkai_cli/render.py`
- `cli/tests/test_render.py`
- `core/gherkai_core/model.py`
- `core/tests/test_lifecycle_states.py`
- `core/tests/test_schedule.py`

## Audit Trail

- EXTRACTED: 257 (82%)
- INFERRED: 55 (18%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*