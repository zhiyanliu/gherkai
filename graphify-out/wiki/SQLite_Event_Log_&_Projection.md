# SQLite Event Log & Projection

> 88 nodes · cohesion 0.06

## Key Concepts

- **test_project.py** (52 connections) — `core/tests/test_project.py`
- **project()** (43 connections) — `core/gherkai_core/project.py`
- **ScopeStarted** (39 connections) — `core/gherkai_core/model.py`
- **project.py** (39 connections) — `core/gherkai_core/project.py`
- **EventRecord** (34 connections) — `core/gherkai_core/project.py`
- **TaskExited** (28 connections) — `core/gherkai_core/project.py`
- **_meta()** (28 connections) — `core/tests/test_project.py`
- **Timing** (24 connections) — `core/gherkai_core/project.py`
- **Action** (21 connections) — `core/gherkai_core/project.py`
- **_exit()** (19 connections) — `core/tests/test_project.py`
- **StepSkipped** (15 connections) — `core/gherkai_core/model.py`
- **_passed_events()** (15 connections) — `core/tests/test_project.py`
- **project_full()** (14 connections) — `core/gherkai_core/project.py`
- **StepStarted** (12 connections) — `core/gherkai_core/model.py`
- **plan_next()** (11 connections) — `core/gherkai_core/project.py`
- **_reduce_scope()** (11 connections) — `core/gherkai_core/project.py`
- **projected_run_status()** (10 connections) — `core/gherkai_core/project.py`
- **_ev()** (10 connections) — `core/tests/test_project.py`
- **sqlite.py** (8 connections) — `core/gherkai_core/adapters/event_log/sqlite.py`
- **test_plan_next_finalize_when_all_terminal()** (8 connections) — `core/tests/test_project.py`
- **test_clean_exit_without_events_converges_with_claimed_baseline()** (7 connections) — `core/tests/test_project.py`
- **test_clean_exit_without_scope_done_is_error()** (7 connections) — `core/tests/test_project.py`
- **test_crash_no_scope_done_nonzero_exit_is_error()** (7 connections) — `core/tests/test_project.py`
- **test_error_clean_exit_incomplete_content_gets_attribution()** (7 connections) — `core/tests/test_project.py`
- **test_plan_next_not_finalize_while_running()** (7 connections) — `core/tests/test_project.py`
- *... and 63 more nodes in this community*

## Relationships

- [Run Result Verdict Model](Run_Result_Verdict_Model.md) (34 shared connections)
- [Event Formatting & Cost Model](Event_Formatting_%26_Cost_Model.md) (33 shared connections)
- [Engine Ports & Adapters](Engine_Ports_%26_Adapters.md) (24 shared connections)
- [Run State Rendering & Boto Guard](Run_State_Rendering_%26_Boto_Guard.md) (23 shared connections)
- [Cloud Launcher & DDB EventLog](Cloud_Launcher_%26_DDB_EventLog.md) (12 shared connections)
- [Conditional Write Contract Tests](Conditional_Write_Contract_Tests.md) (10 shared connections)
- [DynamoDB RunStore Conditional Writes](DynamoDB_RunStore_Conditional_Writes.md) (10 shared connections)
- [Render & ReportStore Local](Render_%26_ReportStore_Local.md) (10 shared connections)
- [Terminal Status Aggregation](Terminal_Status_Aggregation.md) (8 shared connections)
- [SQLite Event Log Store](SQLite_Event_Log_Store.md) (5 shared connections)
- [Run Persistence Orchestration](Run_Persistence_Orchestration.md) (5 shared connections)
- [Wire Protocol Serialization](Wire_Protocol_Serialization.md) (4 shared connections)

## Source Files

- `core/gherkai_core/adapters/event_log/sqlite.py`
- `core/gherkai_core/model.py`
- `core/gherkai_core/project.py`
- `core/tests/test_project.py`

## Audit Trail

- EXTRACTED: 333 (80%)
- INFERRED: 82 (20%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*