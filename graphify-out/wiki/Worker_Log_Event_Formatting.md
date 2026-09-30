# Worker Log Event Formatting

> 163 nodes · cohesion 0.05

## Key Concepts

- **test_schedule.py** (72 connections) — `core/tests/test_schedule.py`
- **schedule()** (62 connections) — `core/gherkai_core/schedule.py`
- **CollectSink** (59 connections) — `core/tests/fake_engine.py`
- **FakeEngine** (56 connections) — `core/tests/fake_engine.py`
- **FakeResolver** (53 connections) — `core/tests/fake_engine.py`
- **_job()** (49 connections) — `core/tests/test_schedule.py`
- **StepDone** (48 connections) — `core/gherkai_core/model.py`
- **_rm()** (48 connections) — `core/tests/test_schedule.py`
- **ScheduleOpts** (46 connections) — `core/gherkai_core/schedule.py`
- **test_lifecycle_states.py** (46 connections) — `core/tests/test_lifecycle_states.py`
- **ScopeDone** (39 connections) — `core/gherkai_core/model.py`
- **ScenarioStarted** (33 connections) — `core/gherkai_core/model.py`
- **ScenarioDone** (32 connections) — `core/gherkai_core/model.py`
- **Votes** (32 connections) — `core/gherkai_core/model.py`
- **_passing_events()** (31 connections) — `core/tests/test_schedule.py`
- **_IncClock** (28 connections) — `core/tests/test_schedule.py`
- **test_subprocess_engine.py** (27 connections) — `core/tests/test_subprocess_engine.py`
- **WorkerNetworkError** (25 connections) — `core/gherkai_core/errors.py`
- **SubprocessEngine** (20 connections) — `core/gherkai_core/adapters/subprocess_engine.py`
- **_NetRaiseEngine** (20 connections) — `core/tests/test_lifecycle_states.py`
- **_AbortProbeEngine** (18 connections) — `core/tests/test_lifecycle_states.py`
- **test_abort_then_clean_eof_is_aborted_not_passed()** (15 connections) — `core/tests/test_schedule.py`
- **_job()** (15 connections) — `core/tests/test_subprocess_engine.py`
- **test_fail_fast_batch_errors()** (14 connections) — `core/tests/test_schedule.py`
- **test_step_skipped_reduced_to_skipped_shortcircuited()** (13 connections) — `core/tests/test_schedule.py`
- *... and 138 more nodes in this community*

## Relationships

- [Result Tree Text Rendering](Result_Tree_Text_Rendering.md) (57 shared connections)
- [Run Definition Domain Model](Run_Definition_Domain_Model.md) (28 shared connections)
- [Event Records Projection](Event_Records_Projection.md) (25 shared connections)
- [Event Wire Serialization](Event_Wire_Serialization.md) (24 shared connections)
- [Core Adapters Documentation](Core_Adapters_Documentation.md) (20 shared connections)
- [Run Persistence Orchestration](Run_Persistence_Orchestration.md) (8 shared connections)
- [Event Gap Grace Tests](Event_Gap_Grace_Tests.md) (6 shared connections)
- [Report Store Adapters](Report_Store_Adapters.md) (6 shared connections)
- [Result Store Serialization](Result_Store_Serialization.md) (6 shared connections)
- [Cloud Composition Helpers](Cloud_Composition_Helpers.md) (4 shared connections)
- [Fargate Worker Handle](Fargate_Worker_Handle.md) (4 shared connections)
- [Reconciler Plan Next](Reconciler_Plan_Next.md) (4 shared connections)

## Source Files

- `cli/gherkai_cli/render.py`
- `cli/tests/test_render.py`
- `core/gherkai_core/adapters/subprocess_engine.py`
- `core/gherkai_core/errors.py`
- `core/gherkai_core/model.py`
- `core/gherkai_core/persist.py`
- `core/gherkai_core/schedule.py`
- `core/tests/fake_engine.py`
- `core/tests/test_lifecycle_states.py`
- `core/tests/test_schedule.py`
- `core/tests/test_subprocess_engine.py`

## Audit Trail

- EXTRACTED: 762 (85%)
- INFERRED: 135 (15%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*