# Event Log & Projection

> 98 nodes · cohesion 0.05

## Key Concepts

- **test_project.py** (59 connections) — `core/tests/test_project.py`
- **ScopeStarted** (45 connections) — `core/gherkai_core/model.py`
- **project()** (45 connections) — `core/gherkai_core/project.py`
- **project.py** (39 connections) — `core/gherkai_core/project.py`
- **EventRecord** (36 connections) — `core/gherkai_core/project.py`
- **_meta()** (32 connections) — `core/tests/test_project.py`
- **TaskExited** (29 connections) — `core/gherkai_core/project.py`
- **Timing** (24 connections) — `core/gherkai_core/project.py`
- **_exit()** (22 connections) — `core/tests/test_project.py`
- **Action** (21 connections) — `core/gherkai_core/project.py`
- **NonTerminalSnapshot** (21 connections) — `core/gherkai_core/project.py`
- **project_full()** (21 connections) — `core/gherkai_core/project.py`
- **_passed_events()** (16 connections) — `core/tests/test_project.py`
- **StepStarted** (15 connections) — `core/gherkai_core/model.py`
- **_aggregate()** (12 connections) — `core/gherkai_core/project.py`
- **_ev()** (12 connections) — `core/tests/test_project.py`
- **plan_next()** (11 connections) — `core/gherkai_core/project.py`
- **_reduce_scope()** (11 connections) — `core/gherkai_core/project.py`
- **test_step_done_message_is_kept_in_step_result()** (11 connections) — `core/tests/test_project.py`
- **sqlite.py** (8 connections) — `core/gherkai_core/adapters/event_log/sqlite.py`
- **test_plan_next_finalize_when_all_terminal()** (8 connections) — `core/tests/test_project.py`
- **test_clean_exit_without_events_converges_with_claimed_baseline()** (7 connections) — `core/tests/test_project.py`
- **test_clean_exit_without_scope_done_is_error()** (7 connections) — `core/tests/test_project.py`
- **test_crash_no_scope_done_nonzero_exit_is_error()** (7 connections) — `core/tests/test_project.py`
- **test_error_clean_exit_incomplete_content_gets_attribution()** (7 connections) — `core/tests/test_project.py`
- *... and 73 more nodes in this community*

## Relationships

- [Event Progress Formatting](Event_Progress_Formatting.md) (47 shared connections)
- [Run State Rendering](Run_State_Rendering.md) (41 shared connections)
- [Run Metadata & S3 Offload](Run_Metadata_%26_S3_Offload.md) (22 shared connections)
- [Explain Rendering Tests](Explain_Rendering_Tests.md) (19 shared connections)
- [S3 Result Store Port](S3_Result_Store_Port.md) (16 shared connections)
- [Conditional Write Contract Tests](Conditional_Write_Contract_Tests.md) (13 shared connections)
- [DynamoDB Event Log](DynamoDB_Event_Log.md) (12 shared connections)
- [Reconcile Orchestration](Reconcile_Orchestration.md) (8 shared connections)
- [SQLite Event Log](SQLite_Event_Log.md) (7 shared connections)
- [Core Typed Errors](Core_Typed_Errors.md) (6 shared connections)
- [Local Result Store](Local_Result_Store.md) (5 shared connections)
- [Run Scheduling Core](Run_Scheduling_Core.md) (4 shared connections)

## Source Files

- `core/gherkai_core/adapters/event_log/sqlite.py`
- `core/gherkai_core/model.py`
- `core/gherkai_core/project.py`
- `core/tests/test_lifecycle_states.py`
- `core/tests/test_project.py`

## Audit Trail

- EXTRACTED: 365 (78%)
- INFERRED: 102 (22%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*