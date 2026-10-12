# Reconciler Event Projection

> 80 nodes · cohesion 0.06

## Key Concepts

- **test_project.py** (59 connections) — `core/tests/test_project.py`
- **ScopeStarted** (45 connections) — `core/gherkai_core/model.py`
- **project()** (44 connections) — `core/gherkai_core/project.py`
- **EventRecord** (36 connections) — `core/gherkai_core/project.py`
- **_meta()** (32 connections) — `core/tests/test_project.py`
- **_exit()** (22 connections) — `core/tests/test_project.py`
- **Action** (21 connections) — `core/gherkai_core/project.py`
- **project_full()** (21 connections) — `core/gherkai_core/project.py`
- **_passed_events()** (16 connections) — `core/tests/test_project.py`
- **_ev()** (12 connections) — `core/tests/test_project.py`
- **plan_next()** (11 connections) — `core/gherkai_core/project.py`
- **test_step_done_message_is_kept_in_step_result()** (11 connections) — `core/tests/test_project.py`
- **finalize_report()** (9 connections) — `core/gherkai_core/reconcile.py`
- **test_plan_next_finalize_when_all_terminal()** (8 connections) — `core/tests/test_project.py`
- **test_clean_exit_without_events_converges_with_claimed_baseline()** (7 connections) — `core/tests/test_project.py`
- **test_clean_exit_without_scope_done_is_error()** (7 connections) — `core/tests/test_project.py`
- **test_crash_no_scope_done_nonzero_exit_is_error()** (7 connections) — `core/tests/test_project.py`
- **test_error_clean_exit_incomplete_content_gets_attribution()** (7 connections) — `core/tests/test_project.py`
- **test_exit_code_none_is_error_not_running()** (7 connections) — `core/tests/test_project.py`
- **test_plan_next_not_finalize_while_running()** (7 connections) — `core/tests/test_project.py`
- **test_plan_next_respects_running_slots()** (7 connections) — `core/tests/test_project.py`
- **test_platform_sentinel_exit_surfaces_reason_in_message()** (7 connections) — `core/tests/test_project.py`
- **test_timed_out_exit_is_error_regardless_of_exit_code_shape()** (7 connections) — `core/tests/test_project.py`
- **test_hwm_across_scopes()** (6 connections) — `core/tests/test_project.py`
- **test_hwm_is_max_worker_seq()** (6 connections) — `core/tests/test_project.py`
- *... and 55 more nodes in this community*

## Relationships

- [Cloud Adapter Boundary Modules](Cloud_Adapter_Boundary_Modules.md) (47 shared connections)
- [Run Scheduling Events Core](Run_Scheduling_Events_Core.md) (15 shared connections)
- [Job Explain Data Model](Job_Explain_Data_Model.md) (14 shared connections)
- [Conditional Write Guards](Conditional_Write_Guards.md) (13 shared connections)
- [DynamoDB Job State Store](DynamoDB_Job_State_Store.md) (6 shared connections)
- [Run State Store](Run_State_Store.md) (6 shared connections)
- [Terminal State Aggregation](Terminal_State_Aggregation.md) (5 shared connections)
- [Run Persistence Local Stores](Run_Persistence_Local_Stores.md) (5 shared connections)
- [EventLog And Launcher Ports](EventLog_And_Launcher_Ports.md) (5 shared connections)
- [Explain Reads And Report Store](Explain_Reads_And_Report_Store.md) (4 shared connections)
- [Cloud Launcher Reconcile Tests](Cloud_Launcher_Reconcile_Tests.md) (4 shared connections)
- [Event Wire Protocol](Event_Wire_Protocol.md) (3 shared connections)

## Source Files

- `core/gherkai_core/model.py`
- `core/gherkai_core/project.py`
- `core/gherkai_core/reconcile.py`
- `core/tests/test_project.py`

## Audit Trail

- EXTRACTED: 301 (86%)
- INFERRED: 50 (14%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*