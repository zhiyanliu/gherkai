# Run State Projection

> 76 nodes · cohesion 0.07

## Key Concepts

- **test_project.py** (59 connections) — `core/tests/test_project.py`
- **ScopeStarted** (45 connections) — `core/gherkai_core/model.py`
- **project()** (44 connections) — `core/gherkai_core/project.py`
- **_meta()** (32 connections) — `core/tests/test_project.py`
- **_exit()** (22 connections) — `core/tests/test_project.py`
- **project_full()** (21 connections) — `core/gherkai_core/project.py`
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
- **test_nonzero_exit_overrides_content_to_error()** (6 connections) — `core/tests/test_project.py`
- **test_out_of_order_records_reduced_by_seq()** (6 connections) — `core/tests/test_project.py`
- *... and 51 more nodes in this community*

## Relationships

- [Event Log Adapters](Event_Log_Adapters.md) (42 shared connections)
- [Job Domain Models](Job_Domain_Models.md) (11 shared connections)
- [Event Formatting](Event_Formatting.md) (8 shared connections)
- [Run State Store](Run_State_Store.md) (7 shared connections)
- [Reconciler Orchestration](Reconciler_Orchestration.md) (7 shared connections)
- [Cloud Store Adapters](Cloud_Store_Adapters.md) (7 shared connections)
- [Local Result Store](Local_Result_Store.md) (5 shared connections)
- [Run Result Aggregation Tree](Run_Result_Aggregation_Tree.md) (4 shared connections)
- [Job Status Severity Aggregation](Job_Status_Severity_Aggregation.md) (3 shared connections)
- [Cloud Reconcile Tests](Cloud_Reconcile_Tests.md) (3 shared connections)
- [Typed Errors and Wire Protocol](Typed_Errors_and_Wire_Protocol.md) (2 shared connections)
- [Fake Worker Test Doubles](Fake_Worker_Test_Doubles.md) (2 shared connections)

## Source Files

- `core/gherkai_core/model.py`
- `core/gherkai_core/project.py`
- `core/tests/test_project.py`

## Audit Trail

- EXTRACTED: 289 (95%)
- INFERRED: 16 (5%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*