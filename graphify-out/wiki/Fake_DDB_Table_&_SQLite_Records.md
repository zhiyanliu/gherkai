# Fake DDB Table & SQLite Records

> 95 nodes · cohesion 0.05

## Key Concepts

- **test_project.py** (59 connections) — `core/tests/test_project.py`
- **ScopeStarted** (45 connections) — `core/gherkai_core/model.py`
- **project()** (44 connections) — `core/gherkai_core/project.py`
- **EventRecord** (36 connections) — `core/gherkai_core/project.py`
- **_meta()** (32 connections) — `core/tests/test_project.py`
- **TaskExited** (29 connections) — `core/gherkai_core/project.py`
- **_exit()** (22 connections) — `core/tests/test_project.py`
- **Action** (21 connections) — `core/gherkai_core/project.py`
- **project_full()** (21 connections) — `core/gherkai_core/project.py`
- **_passed_events()** (16 connections) — `core/tests/test_project.py`
- **StepStarted** (15 connections) — `core/gherkai_core/model.py`
- **_FakeTable** (12 connections) — `cli/tests/test_backend_cloud.py`
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
- **test_exit_code_none_is_error_not_running()** (7 connections) — `core/tests/test_project.py`
- **test_plan_next_not_finalize_while_running()** (7 connections) — `core/tests/test_project.py`
- **test_plan_next_respects_running_slots()** (7 connections) — `core/tests/test_project.py`
- *... and 70 more nodes in this community*

## Relationships

- [Cloud Launcher & Fargate Adapters](Cloud_Launcher_%26_Fargate_Adapters.md) (45 shared connections)
- [Event Progress Formatting](Event_Progress_Formatting.md) (28 shared connections)
- [Run State Rendering & DDB Store](Run_State_Rendering_%26_DDB_Store.md) (20 shared connections)
- [Job/Scenario Explain Model](Job-Scenario_Explain_Model.md) (14 shared connections)
- [Result Rendering & Explain](Result_Rendering_%26_Explain.md) (11 shared connections)
- [SQLite Event Log Adapter](SQLite_Event_Log_Adapter.md) (7 shared connections)
- [Severity Aggregation & Fake Engine](Severity_Aggregation_%26_Fake_Engine.md) (7 shared connections)
- [Job State Serialization](Job_State_Serialization.md) (7 shared connections)
- [DynamoDB Event Log](DynamoDB_Event_Log.md) (6 shared connections)
- [S3 Result Store](S3_Result_Store.md) (5 shared connections)
- [Local Result Store & Persistence](Local_Result_Store_%26_Persistence.md) (5 shared connections)
- [Wire Protocol Serialization](Wire_Protocol_Serialization.md) (4 shared connections)

## Source Files

- `cli/tests/test_backend_cloud.py`
- `core/gherkai_core/adapters/event_log/sqlite.py`
- `core/gherkai_core/model.py`
- `core/gherkai_core/project.py`
- `core/tests/test_project.py`

## Audit Trail

- EXTRACTED: 335 (82%)
- INFERRED: 72 (18%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*