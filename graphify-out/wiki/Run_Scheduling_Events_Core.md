# Run Scheduling Events Core

> 83 nodes · cohesion 0.14

## Key Concepts

- **test_schedule.py** (72 connections) — `core/tests/test_schedule.py`
- **schedule()** (63 connections) — `core/gherkai_core/schedule.py`
- **CollectSink** (60 connections) — `core/tests/fake_engine.py`
- **FakeEngine** (56 connections) — `core/tests/fake_engine.py`
- **FakeResolver** (53 connections) — `core/tests/fake_engine.py`
- **_job()** (49 connections) — `core/tests/test_schedule.py`
- **StepDone** (48 connections) — `core/gherkai_core/model.py`
- **_rm()** (48 connections) — `core/tests/test_schedule.py`
- **ScheduleOpts** (47 connections) — `core/gherkai_core/schedule.py`
- **ScenarioStarted** (33 connections) — `core/gherkai_core/model.py`
- **ScenarioDone** (32 connections) — `core/gherkai_core/model.py`
- **Votes** (32 connections) — `core/gherkai_core/model.py`
- **_passing_events()** (31 connections) — `core/tests/test_schedule.py`
- **_IncClock** (28 connections) — `core/tests/test_schedule.py`
- **_AbortProbeEngine** (18 connections) — `core/tests/test_lifecycle_states.py`
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
- *... and 58 more nodes in this community*

## Relationships

- [Cloud Adapter Boundary Modules](Cloud_Adapter_Boundary_Modules.md) (63 shared connections)
- [Terminal State Aggregation](Terminal_State_Aggregation.md) (43 shared connections)
- [Job Explain Data Model](Job_Explain_Data_Model.md) (19 shared connections)
- [Subprocess Engine Tests](Subprocess_Engine_Tests.md) (16 shared connections)
- [Reconciler Event Projection](Reconciler_Event_Projection.md) (15 shared connections)
- [Event Progress Formatting](Event_Progress_Formatting.md) (9 shared connections)
- [Event Wire Protocol](Event_Wire_Protocol.md) (7 shared connections)
- [Run Persistence Local Stores](Run_Persistence_Local_Stores.md) (7 shared connections)
- [Explain Reads And Report Store](Explain_Reads_And_Report_Store.md) (7 shared connections)
- [Result Tree Rendering](Result_Tree_Rendering.md) (3 shared connections)
- [S3 Result Store](S3_Result_Store.md) (3 shared connections)
- [Fargate Worker Handle](Fargate_Worker_Handle.md) (2 shared connections)

## Source Files

- `core/gherkai_core/model.py`
- `core/gherkai_core/schedule.py`
- `core/gherkai_core/wire.py`
- `core/tests/fake_engine.py`
- `core/tests/test_lifecycle_states.py`
- `core/tests/test_schedule.py`

## Audit Trail

- EXTRACTED: 593 (88%)
- INFERRED: 83 (12%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*