# Event Formatting

> 30 nodes · cohesion 0.13

## Key Concepts

- **StepDone** (48 connections) — `core/gherkai_core/model.py`
- **ScenarioStarted** (33 connections) — `core/gherkai_core/model.py`
- **ScenarioDone** (32 connections) — `core/gherkai_core/model.py`
- **Votes** (32 connections) — `core/gherkai_core/model.py`
- **_IncClock** (28 connections) — `core/tests/test_schedule.py`
- **_AbortProbeEngine** (18 connections) — `core/tests/test_lifecycle_states.py`
- **test_failed_and_error_steps_cost_still_aggregated()** (12 connections) — `core/tests/test_schedule.py`
- **test_partial_completion_without_scope_done_not_passed()** (12 connections) — `core/tests/test_schedule.py`
- **Cost** (10 connections) — `core/gherkai_core/model.py`
- **_full_timed_events()** (9 connections) — `core/tests/test_schedule.py`
- **_events_with_time()** (8 connections) — `core/tests/test_schedule.py`
- **_events_with_tokens()** (8 connections) — `core/tests/test_schedule.py`
- **_failing_events()** (8 connections) — `core/tests/test_schedule.py`
- **format_event()** (6 connections) — `cli/gherkai_cli/render.py`
- **test_format_event_step_done_with_votes_and_cost()** (5 connections) — `cli/tests/test_render.py`
- **test_format_event_single_vote_hides_tally()** (4 connections) — `cli/tests/test_render.py`
- **._gen()** (4 connections) — `core/tests/test_lifecycle_states.py`
- **test_format_event_omits_scope_id()** (3 connections) — `cli/tests/test_render.py`
- **Event** (1 connections)
- **单个 ADR 0024 事件 → 一行进度文本（不含 scope_id——scope 归调用方的 `[core <scope>:event]` 前缀， 见…** (1 connections) — `cli/gherkai_cli/render.py`
- **AI 断言的投票 tally（ADR 0024）。存在与否即 core 区分「AI 断言 vs 其余」的依据。** (1 connections) — `core/gherkai_core/model.py`
- **step 级成本：engine 只报**原生量**，平铺、各 optional（ADR 0024）。 原则：core…** (1 connections) — `core/gherkai_core/model.py`
- **.__init__()** (1 connections) — `core/tests/test_lifecycle_states.py`
- **.__call__()** (1 connections) — `core/tests/test_schedule.py`
- **.__init__()** (1 connections) — `core/tests/test_schedule.py`
- *... and 5 more nodes in this community*

## Relationships

- [Run Scheduling Core](Run_Scheduling_Core.md) (82 shared connections)
- [Event Log Adapters](Event_Log_Adapters.md) (26 shared connections)
- [Typed Errors and Wire Protocol](Typed_Errors_and_Wire_Protocol.md) (14 shared connections)
- [Job Domain Models](Job_Domain_Models.md) (10 shared connections)
- [Run Result Aggregation Tree](Run_Result_Aggregation_Tree.md) (8 shared connections)
- [Run State Projection](Run_State_Projection.md) (8 shared connections)
- [Local Result Store](Local_Result_Store.md) (6 shared connections)
- [Job Status Severity Aggregation](Job_Status_Severity_Aggregation.md) (5 shared connections)
- [Fake Worker Test Doubles](Fake_Worker_Test_Doubles.md) (5 shared connections)
- [Cloud Store Adapters](Cloud_Store_Adapters.md) (4 shared connections)
- [Fargate Worker Handle](Fargate_Worker_Handle.md) (2 shared connections)
- [Event Gap & ECS Polling](Event_Gap_%26_ECS_Polling.md) (2 shared connections)

## Source Files

- `cli/gherkai_cli/render.py`
- `cli/tests/test_render.py`
- `core/gherkai_core/model.py`
- `core/tests/test_lifecycle_states.py`
- `core/tests/test_schedule.py`

## Audit Trail

- EXTRACTED: 179 (76%)
- INFERRED: 57 (24%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*