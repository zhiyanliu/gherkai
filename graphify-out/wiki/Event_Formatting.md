# Event Formatting

> 46 nodes · cohesion 0.10

## Key Concepts

- **StepDone** (48 connections) — `core/gherkai_core/model.py`
- **ScopeDone** (40 connections) — `core/gherkai_core/model.py`
- **project.py** (39 connections) — `core/gherkai_core/project.py`
- **ScenarioStarted** (33 connections) — `core/gherkai_core/model.py`
- **ScenarioDone** (32 connections) — `core/gherkai_core/model.py`
- **TaskExited** (29 connections) — `core/gherkai_core/project.py`
- **Timing** (24 connections) — `core/gherkai_core/project.py`
- **Action** (21 connections) — `core/gherkai_core/project.py`
- **NonTerminalSnapshot** (21 connections) — `core/gherkai_core/project.py`
- **_AbortProbeEngine** (18 connections) — `core/tests/test_lifecycle_states.py`
- **StepSkipped** (16 connections) — `core/gherkai_core/model.py`
- **StepStarted** (15 connections) — `core/gherkai_core/model.py`
- **test_step_skipped_reduced_to_skipped_shortcircuited()** (13 connections) — `core/tests/test_schedule.py`
- **test_step_skipped_does_not_pollute_scenario_or_run_status()** (12 connections) — `core/tests/test_schedule.py`
- **test_step_skipped_without_scenario_done_still_recorded()** (12 connections) — `core/tests/test_schedule.py`
- **reduce_event()** (11 connections) — `core/gherkai_core/project.py`
- **_reduce_scope()** (11 connections) — `core/gherkai_core/project.py`
- **_full_timed_events()** (9 connections) — `core/tests/test_schedule.py`
- **_events_with_time()** (8 connections) — `core/tests/test_schedule.py`
- **_events_with_tokens()** (8 connections) — `core/tests/test_schedule.py`
- **_failing_events()** (8 connections) — `core/tests/test_schedule.py`
- **test_on_event_runs_only_on_scope_started()** (7 connections) — `core/tests/test_persist.py`
- **format_event()** (6 connections) — `cli/gherkai_cli/render.py`
- **_job_status()** (6 connections) — `core/gherkai_core/project.py`
- **test_format_event_step_done_with_votes_and_cost()** (5 connections) — `cli/tests/test_render.py`
- *... and 21 more nodes in this community*

## Relationships

- [Schedule Core & Fakes](Schedule_Core_%26_Fakes.md) (91 shared connections)
- [Cloud Boto3 Guards & EventLog](Cloud_Boto3_Guards_%26_EventLog.md) (51 shared connections)
- [Run State Projection](Run_State_Projection.md) (43 shared connections)
- [Text Render & Wording Guards](Text_Render_%26_Wording_Guards.md) (14 shared connections)
- [Job Explain & S3 Offload](Job_Explain_%26_S3_Offload.md) (11 shared connections)
- [Typed Errors & Severity](Typed_Errors_%26_Severity.md) (10 shared connections)
- [Fargate Worker Handle](Fargate_Worker_Handle.md) (9 shared connections)
- [S3 Result Store](S3_Result_Store.md) (8 shared connections)
- [Local Report Store](Local_Report_Store.md) (6 shared connections)
- [Local Result Store & Persistence](Local_Result_Store_%26_Persistence.md) (5 shared connections)
- [DynamoDB RunStore Adapter](DynamoDB_RunStore_Adapter.md) (5 shared connections)
- [Run State Rendering](Run_State_Rendering.md) (5 shared connections)

## Source Files

- `cli/gherkai_cli/render.py`
- `cli/tests/test_render.py`
- `core/gherkai_core/model.py`
- `core/gherkai_core/project.py`
- `core/tests/test_lifecycle_states.py`
- `core/tests/test_persist.py`
- `core/tests/test_schedule.py`

## Audit Trail

- EXTRACTED: 264 (70%)
- INFERRED: 113 (30%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*