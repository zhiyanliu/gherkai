# Local Result Store & Persistence

> 31 nodes · cohesion 0.13

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
- **build_local_stores()** (6 connections) — `runtime/gherkai_runtime/compose.py`
- **.on_event()** (5 connections) — `core/gherkai_core/persist.py`
- **test_begin_writes_all_pending_initial_state()** (4 connections) — `core/tests/test_persist.py`
- **test_on_job_complete_saves_result_before_job_state()** (4 connections) — `core/tests/test_persist.py`
- **.finalize()** (3 connections) — `core/gherkai_core/persist.py`
- **.__init__()** (2 connections) — `core/gherkai_core/adapters/result_store/local.py`
- **.preflight()** (2 connections) — `core/gherkai_core/adapters/result_store/local.py`
- **Path** (1 connections)
- **ResultStore 的本地文件实现（组合根注入；S3 实装见同包 `s3.py`）。** (1 connections) — `core/gherkai_core/adapters/result_store/local.py`
- **探活 no-op（ADR 0030 决定七）：本地文件后端无「桶不存在」问题，目录随写随建。** (1 connections) — `core/gherkai_core/adapters/result_store/local.py`
- **Event** (1 connections)
- **run 结束（schedule 返回后）：commit point。 写总 status + ended_at（finalize_run 就是 commit…** (1 connections) — `core/gherkai_core/persist.py`
- *... and 6 more nodes in this community*

## Relationships

- [Cloud Launcher & Fargate Adapters](Cloud_Launcher_%26_Fargate_Adapters.md) (13 shared connections)
- [S3 Result Store](S3_Result_Store.md) (7 shared connections)
- [SQLite Event Log Adapter](SQLite_Event_Log_Adapter.md) (7 shared connections)
- [Event Progress Formatting](Event_Progress_Formatting.md) (7 shared connections)
- [Result Rendering & Explain](Result_Rendering_%26_Explain.md) (6 shared connections)
- [Local Result Store](Local_Result_Store.md) (5 shared connections)
- [Job State Serialization](Job_State_Serialization.md) (5 shared connections)
- [Fake DDB Table & SQLite Records](Fake_DDB_Table_%26_SQLite_Records.md) (5 shared connections)
- [Job/Scenario Explain Model](Job-Scenario_Explain_Model.md) (3 shared connections)
- [Run State Rendering & DDB Store](Run_State_Rendering_%26_DDB_Store.md) (2 shared connections)
- [Atomic Local File Writes](Atomic_Local_File_Writes.md) (1 shared connections)
- [CLI Command Dispatch Entry](CLI_Command_Dispatch_Entry.md) (1 shared connections)

## Source Files

- `core/gherkai_core/adapters/result_store/local.py`
- `core/gherkai_core/persist.py`
- `core/tests/test_persist.py`
- `runtime/gherkai_runtime/compose.py`

## Audit Trail

- EXTRACTED: 111 (87%)
- INFERRED: 16 (13%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*