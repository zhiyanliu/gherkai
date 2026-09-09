# Local Result Store

> 39 nodes · cohesion 0.09

## Key Concepts

- **RunPersistence** (28 connections) — `core/gherkai_core/persist.py`
- **test_persist.py** (27 connections) — `core/tests/test_persist.py`
- **LocalResultStore** (19 connections) — `core/gherkai_core/adapters/result_store/local.py`
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
- **.on_event()** (5 connections) — `core/gherkai_core/persist.py`
- **.on_job_complete()** (5 connections) — `core/gherkai_core/persist.py`
- **.load_all()** (4 connections) — `core/gherkai_core/adapters/result_store/local.py`
- **.load_job_result()** (4 connections) — `core/gherkai_core/adapters/result_store/local.py`
- **.save_job_result()** (4 connections) — `core/gherkai_core/adapters/result_store/local.py`
- **test_begin_writes_all_pending_initial_state()** (4 connections) — `core/tests/test_persist.py`
- **test_on_job_complete_saves_result_before_job_state()** (4 connections) — `core/tests/test_persist.py`
- **result_store/__init__.py** (3 connections) — `core/gherkai_core/adapters/result_store/__init__.py`
- **.finalize()** (3 connections) — `core/gherkai_core/persist.py`
- **.__init__()** (2 connections) — `core/gherkai_core/adapters/result_store/local.py`
- **.preflight()** (2 connections) — `core/gherkai_core/adapters/result_store/local.py`
- **ResultStore adapters（ADR 0016）。当前只有 local；未来对象存储。** (1 connections) — `core/gherkai_core/adapters/result_store/__init__.py`
- *... and 14 more nodes in this community*

## Relationships

- [Run Result Rendering](Run_Result_Rendering.md) (23 shared connections)
- [Run State Rendering](Run_State_Rendering.md) (8 shared connections)
- [Event Progress Formatting](Event_Progress_Formatting.md) (7 shared connections)
- [Local Run Store](Local_Run_Store.md) (6 shared connections)
- [S3 Result Store](S3_Result_Store.md) (5 shared connections)
- [State Projection & Planning](State_Projection_%26_Planning.md) (5 shared connections)
- [Engine Ports & Adapters](Engine_Ports_%26_Adapters.md) (4 shared connections)
- [Boto Guard & S3 Offload](Boto_Guard_%26_S3_Offload.md) (3 shared connections)
- [Store Composition & Step Query](Store_Composition_%26_Step_Query.md) (1 shared connections)
- [Cloud Submit Preflight Gates](Cloud_Submit_Preflight_Gates.md) (1 shared connections)
- [Run Scheduling Engine](Run_Scheduling_Engine.md) (1 shared connections)

## Source Files

- `core/gherkai_core/adapters/result_store/__init__.py`
- `core/gherkai_core/adapters/result_store/local.py`
- `core/gherkai_core/persist.py`
- `core/tests/test_persist.py`

## Audit Trail

- EXTRACTED: 119 (89%)
- INFERRED: 15 (11%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*