# Run State Projection

> 80 nodes · cohesion 0.06

## Key Concepts

- **test_project.py** (59 connections) — `core/tests/test_project.py`
- **ScopeStarted** (45 connections) — `core/gherkai_core/model.py`
- **project()** (44 connections) — `core/gherkai_core/project.py`
- **EventRecord** (36 connections) — `core/gherkai_core/project.py`
- **_meta()** (32 connections) — `core/tests/test_project.py`
- **_exit()** (22 connections) — `core/tests/test_project.py`
- **project_full()** (21 connections) — `core/gherkai_core/project.py`
- **reconcile.py** (17 connections) — `core/gherkai_core/reconcile.py`
- **_passed_events()** (16 connections) — `core/tests/test_project.py`
- **_ev()** (12 connections) — `core/tests/test_project.py`
- **plan_next()** (11 connections) — `core/gherkai_core/project.py`
- **test_step_done_message_is_kept_in_step_result()** (11 connections) — `core/tests/test_project.py`
- **projected_run_status()** (10 connections) — `core/gherkai_core/project.py`
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

- [Event Formatting](Event_Formatting.md) (43 shared connections)
- [Cloud Boto3 Guards & EventLog](Cloud_Boto3_Guards_%26_EventLog.md) (14 shared connections)
- [Conditional Write Tests](Conditional_Write_Tests.md) (13 shared connections)
- [Job Explain & S3 Offload](Job_Explain_%26_S3_Offload.md) (13 shared connections)
- [Reconciler Ports](Reconciler_Ports.md) (9 shared connections)
- [DynamoDB RunStore Adapter](DynamoDB_RunStore_Adapter.md) (8 shared connections)
- [Run State Rendering](Run_State_Rendering.md) (6 shared connections)
- [Typed Errors & Severity](Typed_Errors_%26_Severity.md) (5 shared connections)
- [Local Result Store & Persistence](Local_Result_Store_%26_Persistence.md) (4 shared connections)
- [Fargate Worker Handle](Fargate_Worker_Handle.md) (4 shared connections)
- [Cloud Job Launcher](Cloud_Job_Launcher.md) (4 shared connections)
- [SQLite Event Log](SQLite_Event_Log.md) (3 shared connections)

## Source Files

- `core/gherkai_core/model.py`
- `core/gherkai_core/project.py`
- `core/gherkai_core/reconcile.py`
- `core/tests/test_project.py`

## Audit Trail

- EXTRACTED: 314 (90%)
- INFERRED: 33 (10%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*