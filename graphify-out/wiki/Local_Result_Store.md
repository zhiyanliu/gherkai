# Local Result Store

> 37 nodes · cohesion 0.10

## Key Concepts

- **RunPersistence** (31 connections) — `core/gherkai_core/persist.py`
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
- **.on_event()** (5 connections) — `core/gherkai_core/persist.py`
- **.on_job_complete()** (5 connections) — `core/gherkai_core/persist.py`
- **.load_all()** (4 connections) — `core/gherkai_core/adapters/result_store/local.py`
- **.load_job_result()** (4 connections) — `core/gherkai_core/adapters/result_store/local.py`
- **test_begin_writes_all_pending_initial_state()** (4 connections) — `core/tests/test_persist.py`
- **test_on_job_complete_saves_result_before_job_state()** (4 connections) — `core/tests/test_persist.py`
- **result_store/__init__.py** (3 connections) — `core/gherkai_core/adapters/result_store/__init__.py`
- **.__init__()** (2 connections) — `core/gherkai_core/adapters/result_store/local.py`
- **.preflight()** (2 connections) — `core/gherkai_core/adapters/result_store/local.py`
- **ResultStore adapters（ADR 0016）：local（本包 `local.py`）+ S3（`s3.py`，ADR 0030 决定六）。…** (1 connections) — `core/gherkai_core/adapters/result_store/__init__.py`
- **Path** (1 connections)
- *... and 12 more nodes in this community*

## Relationships

- [Run State Rendering](Run_State_Rendering.md) (14 shared connections)
- [Local & S3 Result Stores](Local_%26_S3_Result_Stores.md) (12 shared connections)
- [S3 Result Store Port](S3_Result_Store_Port.md) (11 shared connections)
- [Event Progress Formatting](Event_Progress_Formatting.md) (7 shared connections)
- [Explain Rendering Tests](Explain_Rendering_Tests.md) (6 shared connections)
- [Run Metadata & S3 Offload](Run_Metadata_%26_S3_Offload.md) (6 shared connections)
- [Event Log & Projection](Event_Log_%26_Projection.md) (5 shared connections)
- [Atomic Result Store](Atomic_Result_Store.md) (3 shared connections)
- [Worker Capability Query](Worker_Capability_Query.md) (1 shared connections)
- [Local Reconcile Rebuild](Local_Reconcile_Rebuild.md) (1 shared connections)
- [Atomic File Writes](Atomic_File_Writes.md) (1 shared connections)
- [Run & Submit Commands](Run_%26_Submit_Commands.md) (1 shared connections)

## Source Files

- `core/gherkai_core/adapters/result_store/__init__.py`
- `core/gherkai_core/adapters/result_store/local.py`
- `core/gherkai_core/persist.py`
- `core/tests/test_persist.py`

## Audit Trail

- EXTRACTED: 124 (89%)
- INFERRED: 15 (11%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*