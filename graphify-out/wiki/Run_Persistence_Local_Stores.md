# Run Persistence Local Stores

> 36 nodes · cohesion 0.11

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
- **.on_event()** (5 connections) — `core/gherkai_core/persist.py`
- **test_job_result_file_stays_readable_by_others()** (4 connections) — `core/tests/test_local_result_store_atomic.py`
- **test_begin_writes_all_pending_initial_state()** (4 connections) — `core/tests/test_persist.py`
- **test_on_job_complete_saves_result_before_job_state()** (4 connections) — `core/tests/test_persist.py`
- **test_concurrent_reader_never_sees_torn_job_result()** (3 connections) — `core/tests/test_local_result_store_atomic.py`
- **.__init__()** (2 connections) — `core/gherkai_core/adapters/result_store/local.py`
- **.preflight()** (2 connections) — `core/gherkai_core/adapters/result_store/local.py`
- **Path** (1 connections)
- **ResultStore 的本地文件实现（组合根注入；S3 实装见同包 `s3.py`）。** (1 connections) — `core/gherkai_core/adapters/result_store/local.py`
- *... and 11 more nodes in this community*

## Relationships

- [Run State Store](Run_State_Store.md) (9 shared connections)
- [S3 Result Store](S3_Result_Store.md) (8 shared connections)
- [Cloud Adapter Boundary Modules](Cloud_Adapter_Boundary_Modules.md) (8 shared connections)
- [Job Explain Data Model](Job_Explain_Data_Model.md) (8 shared connections)
- [Run Scheduling Events Core](Run_Scheduling_Events_Core.md) (7 shared connections)
- [Explain Reads And Report Store](Explain_Reads_And_Report_Store.md) (7 shared connections)
- [Result Tree Rendering](Result_Tree_Rendering.md) (6 shared connections)
- [Result Store Adapters](Result_Store_Adapters.md) (5 shared connections)
- [Reconciler Event Projection](Reconciler_Event_Projection.md) (5 shared connections)
- [DynamoDB Job State Store](DynamoDB_Job_State_Store.md) (4 shared connections)
- [Store Port Definitions](Store_Port_Definitions.md) (3 shared connections)
- [Atomic Local Writes](Atomic_Local_Writes.md) (1 shared connections)

## Source Files

- `core/gherkai_core/adapters/result_store/local.py`
- `core/gherkai_core/persist.py`
- `core/tests/test_local_result_store_atomic.py`
- `core/tests/test_persist.py`
- `runtime/gherkai_runtime/compose.py`

## Audit Trail

- EXTRACTED: 130 (89%)
- INFERRED: 16 (11%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*