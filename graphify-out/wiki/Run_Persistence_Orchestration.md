# Run Persistence Orchestration

> 39 nodes · cohesion 0.10

## Key Concepts

- **RunPersistence** (28 connections) — `core/gherkai_core/persist.py`
- **test_persist.py** (27 connections) — `core/tests/test_persist.py`
- **LocalResultStore** (22 connections) — `core/gherkai_core/adapters/result_store/local.py`
- **test_local_result_store_atomic.py** (13 connections) — `core/tests/test_local_result_store_atomic.py`
- **_jr()** (11 connections) — `core/tests/test_persist.py`
- **_meta()** (10 connections) — `core/tests/test_persist.py`
- **_big_job_result()** (9 connections) — `core/tests/test_local_result_store_atomic.py`
- **test_running_phase_has_no_data_plane_file_until_complete()** (8 connections) — `core/tests/test_persist.py`
- **_recording()** (7 connections) — `core/tests/test_persist.py`
- **test_aborted_job_preserves_session_id_through_realtime_write()** (7 connections) — `core/tests/test_persist.py`
- **test_finalize_isolates_report_write_failure()** (7 connections) — `core/tests/test_persist.py`
- **test_on_event_runs_only_on_scope_started()** (7 connections) — `core/tests/test_persist.py`
- **test_aborted_with_none_session_does_not_resurrect_but_documents_edge()** (6 connections) — `core/tests/test_persist.py`
- **test_finalize_with_report_store_returns_uri()** (6 connections) — `core/tests/test_persist.py`
- **test_finalize_without_report_store_returns_none()** (6 connections) — `core/tests/test_persist.py`
- **build_local_stores()** (6 connections) — `runtime/gherkai_runtime/compose.py`
- **.on_job_complete()** (5 connections) — `core/gherkai_core/persist.py`
- **test_job_result_file_stays_readable_by_others()** (4 connections) — `core/tests/test_local_result_store_atomic.py`
- **test_begin_writes_all_pending_initial_state()** (4 connections) — `core/tests/test_persist.py`
- **test_on_job_complete_saves_result_before_job_state()** (4 connections) — `core/tests/test_persist.py`
- **result_store/__init__.py** (3 connections) — `core/gherkai_core/adapters/result_store/__init__.py`
- **.finalize()** (3 connections) — `core/gherkai_core/persist.py`
- **test_concurrent_reader_never_sees_torn_job_result()** (3 connections) — `core/tests/test_local_result_store_atomic.py`
- **.__init__()** (2 connections) — `core/gherkai_core/adapters/result_store/local.py`
- **.preflight()** (2 connections) — `core/gherkai_core/adapters/result_store/local.py`
- *... and 14 more nodes in this community*

## Relationships

- [Result Tree Text Rendering](Result_Tree_Text_Rendering.md) (21 shared connections)
- [Run State Rendering](Run_State_Rendering.md) (10 shared connections)
- [Core Adapters Documentation](Core_Adapters_Documentation.md) (8 shared connections)
- [Worker Log Event Formatting](Worker_Log_Event_Formatting.md) (8 shared connections)
- [Run Definition Domain Model](Run_Definition_Domain_Model.md) (8 shared connections)
- [Result Store Serialization](Result_Store_Serialization.md) (5 shared connections)
- [Event Records Projection](Event_Records_Projection.md) (5 shared connections)
- [Report Store Adapters](Report_Store_Adapters.md) (3 shared connections)
- [DynamoDB Run Store](DynamoDB_Run_Store.md) (2 shared connections)
- [S3 Result Store](S3_Result_Store.md) (1 shared connections)
- [Atomic Local Writes](Atomic_Local_Writes.md) (1 shared connections)
- [Local Reconcile Rebuild](Local_Reconcile_Rebuild.md) (1 shared connections)

## Source Files

- `core/gherkai_core/adapters/result_store/__init__.py`
- `core/gherkai_core/adapters/result_store/local.py`
- `core/gherkai_core/persist.py`
- `core/tests/test_local_result_store_atomic.py`
- `core/tests/test_persist.py`
- `runtime/gherkai_runtime/compose.py`

## Audit Trail

- EXTRACTED: 133 (89%)
- INFERRED: 17 (11%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*