# Local Result Store

> 41 nodes · cohesion 0.09

## Key Concepts

- **RunPersistence** (28 connections) — `core/gherkai_core/persist.py`
- **test_persist.py** (27 connections) — `core/tests/test_persist.py`
- **LocalResultStore** (22 connections) — `core/gherkai_core/adapters/result_store/local.py`
- **_jr()** (11 connections) — `core/tests/test_persist.py`
- **_meta()** (10 connections) — `core/tests/test_persist.py`
- **test_running_phase_has_no_data_plane_file_until_complete()** (8 connections) — `core/tests/test_persist.py`
- **_recording()** (7 connections) — `core/tests/test_persist.py`
- **test_aborted_job_preserves_session_id_through_realtime_write()** (7 connections) — `core/tests/test_persist.py`
- **test_finalize_isolates_report_write_failure()** (7 connections) — `core/tests/test_persist.py`
- **test_on_event_runs_only_on_scope_started()** (7 connections) — `core/tests/test_persist.py`
- **test_aborted_with_none_session_does_not_resurrect_but_documents_edge()** (6 connections) — `core/tests/test_persist.py`
- **test_finalize_with_report_store_returns_uri()** (6 connections) — `core/tests/test_persist.py`
- **test_finalize_without_report_store_returns_none()** (6 connections) — `core/tests/test_persist.py`
- **.save_job_result()** (5 connections) — `core/gherkai_core/adapters/result_store/local.py`
- **.begin()** (5 connections) — `core/gherkai_core/persist.py`
- **.on_event()** (5 connections) — `core/gherkai_core/persist.py`
- **.on_job_complete()** (5 connections) — `core/gherkai_core/persist.py`
- **.load_all()** (4 connections) — `core/gherkai_core/adapters/result_store/local.py`
- **.load_job_result()** (4 connections) — `core/gherkai_core/adapters/result_store/local.py`
- **test_begin_writes_all_pending_initial_state()** (4 connections) — `core/tests/test_persist.py`
- **test_on_job_complete_saves_result_before_job_state()** (4 connections) — `core/tests/test_persist.py`
- **result_store/__init__.py** (3 connections) — `core/gherkai_core/adapters/result_store/__init__.py`
- **.finalize()** (3 connections) — `core/gherkai_core/persist.py`
- **.__init__()** (2 connections) — `core/gherkai_core/adapters/result_store/local.py`
- **.preflight()** (2 connections) — `core/gherkai_core/adapters/result_store/local.py`
- *... and 16 more nodes in this community*

## Relationships

- [Run Result Aggregation Tree](Run_Result_Aggregation_Tree.md) (23 shared connections)
- [Cloud Store Adapters](Cloud_Store_Adapters.md) (12 shared connections)
- [Job Domain Models](Job_Domain_Models.md) (8 shared connections)
- [Run Store Adapters](Run_Store_Adapters.md) (6 shared connections)
- [Event Formatting](Event_Formatting.md) (6 shared connections)
- [Run State Projection](Run_State_Projection.md) (5 shared connections)
- [Result Store & Report Refs](Result_Store_%26_Report_Refs.md) (3 shared connections)
- [Run State Store](Run_State_Store.md) (2 shared connections)
- [Run Scheduling Core](Run_Scheduling_Core.md) (2 shared connections)
- [Local Detached Execution](Local_Detached_Execution.md) (1 shared connections)
- [Atomic Write and Report Stores](Atomic_Write_and_Report_Stores.md) (1 shared connections)
- [CLI Command Handlers](CLI_Command_Handlers.md) (1 shared connections)

## Source Files

- `core/gherkai_core/adapters/result_store/__init__.py`
- `core/gherkai_core/adapters/result_store/local.py`
- `core/gherkai_core/persist.py`
- `core/tests/test_persist.py`

## Audit Trail

- EXTRACTED: 127 (89%)
- INFERRED: 15 (11%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*