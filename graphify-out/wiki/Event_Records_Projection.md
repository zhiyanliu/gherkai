# Event Records Projection

> 54 nodes · cohesion 0.09

## Key Concepts

- **test_project.py** (59 connections) — `core/tests/test_project.py`
- **ScopeStarted** (42 connections) — `core/gherkai_core/model.py`
- **EventRecord** (36 connections) — `core/gherkai_core/project.py`
- **_meta()** (32 connections) — `core/tests/test_project.py`
- **TaskExited** (29 connections) — `core/gherkai_core/project.py`
- **_exit()** (22 connections) — `core/tests/test_project.py`
- **project_full()** (21 connections) — `core/gherkai_core/project.py`
- **StepStarted** (15 connections) — `core/gherkai_core/model.py`
- **_ev()** (12 connections) — `core/tests/test_project.py`
- **test_step_done_message_is_kept_in_step_result()** (11 connections) — `core/tests/test_project.py`
- **.records()** (7 connections) — `core/gherkai_core/adapters/event_log/ddb.py`
- **test_clean_exit_without_events_converges_with_claimed_baseline()** (7 connections) — `core/tests/test_project.py`
- **test_clean_exit_without_scope_done_is_error()** (7 connections) — `core/tests/test_project.py`
- **test_crash_no_scope_done_nonzero_exit_is_error()** (7 connections) — `core/tests/test_project.py`
- **test_error_clean_exit_incomplete_content_gets_attribution()** (7 connections) — `core/tests/test_project.py`
- **test_exit_code_none_is_error_not_running()** (7 connections) — `core/tests/test_project.py`
- **test_plan_next_not_finalize_while_running()** (7 connections) — `core/tests/test_project.py`
- **test_plan_next_respects_running_slots()** (7 connections) — `core/tests/test_project.py`
- **test_platform_sentinel_exit_surfaces_reason_in_message()** (7 connections) — `core/tests/test_project.py`
- **test_timed_out_exit_is_error_regardless_of_exit_code_shape()** (7 connections) — `core/tests/test_project.py`
- **.records()** (6 connections) — `core/gherkai_core/adapters/event_log/sqlite.py`
- **test_project_full_carries_run_duration_from_host()** (6 connections) — `core/tests/test_project.py`
- **test_project_full_refuses_non_terminal_snapshot()** (6 connections) — `core/tests/test_project.py`
- **test_scope_started_running_without_exit()** (6 connections) — `core/tests/test_project.py`
- **test_timed_out_attribution_error_type_timeout()** (6 connections) — `core/tests/test_project.py`
- *... and 29 more nodes in this community*

## Relationships

- [State Projection Tests](State_Projection_Tests.md) (41 shared connections)
- [Result Tree Text Rendering](Result_Tree_Text_Rendering.md) (28 shared connections)
- [Worker Log Event Formatting](Worker_Log_Event_Formatting.md) (25 shared connections)
- [Run Definition Domain Model](Run_Definition_Domain_Model.md) (12 shared connections)
- [Reconciler Plan Next](Reconciler_Plan_Next.md) (11 shared connections)
- [Event Wire Serialization](Event_Wire_Serialization.md) (8 shared connections)
- [Conditional Write Tests](Conditional_Write_Tests.md) (8 shared connections)
- [SQLite Event Log](SQLite_Event_Log.md) (6 shared connections)
- [Run Persistence Orchestration](Run_Persistence_Orchestration.md) (5 shared connections)
- [Core Adapters Documentation](Core_Adapters_Documentation.md) (5 shared connections)
- [DynamoDB Run Store](DynamoDB_Run_Store.md) (4 shared connections)
- [Run State Rendering](Run_State_Rendering.md) (4 shared connections)

## Source Files

- `core/gherkai_core/adapters/event_log/ddb.py`
- `core/gherkai_core/adapters/event_log/sqlite.py`
- `core/gherkai_core/model.py`
- `core/gherkai_core/project.py`
- `core/tests/test_project.py`

## Audit Trail

- EXTRACTED: 250 (83%)
- INFERRED: 52 (17%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*