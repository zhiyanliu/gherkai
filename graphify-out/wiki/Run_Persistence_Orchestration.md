# Run Persistence Orchestration

> 30 nodes · cohesion 0.14

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
- **.on_job_complete()** (5 connections) — `core/gherkai_core/persist.py`
- **test_begin_writes_all_pending_initial_state()** (4 connections) — `core/tests/test_persist.py`
- **test_on_job_complete_saves_result_before_job_state()** (4 connections) — `core/tests/test_persist.py`
- **result_store/__init__.py** (3 connections) — `core/gherkai_core/adapters/result_store/__init__.py`
- **.finalize()** (3 connections) — `core/gherkai_core/persist.py`
- **.__init__()** (2 connections) — `core/gherkai_core/adapters/result_store/local.py`
- **.preflight()** (2 connections) — `core/gherkai_core/adapters/result_store/local.py`
- **ResultStore adapters（ADR 0016）。当前只有 local；未来对象存储。** (1 connections) — `core/gherkai_core/adapters/result_store/__init__.py`
- **Path** (1 connections)
- **ResultStore 的本地文件实现（组合根注入；未来对象存储版换落点）。** (1 connections) — `core/gherkai_core/adapters/result_store/local.py`
- **探活 no-op（ADR 0030 决定七）：本地文件后端无「桶不存在」问题，目录随写随建。** (1 connections) — `core/gherkai_core/adapters/result_store/local.py`
- **run 结束（schedule 返回后）：commit point。 写总 status + ended_at（finalize_run = commit…** (1 connections) — `core/gherkai_core/persist.py`
- *... and 5 more nodes in this community*

## Relationships

- [Run Result Verdict Model](Run_Result_Verdict_Model.md) (19 shared connections)
- [DynamoDB RunStore Conditional Writes](DynamoDB_RunStore_Conditional_Writes.md) (10 shared connections)
- [Run State Rendering & Boto Guard](Run_State_Rendering_%26_Boto_Guard.md) (6 shared connections)
- [Event Formatting & Cost Model](Event_Formatting_%26_Cost_Model.md) (6 shared connections)
- [ResultStore Local/S3](ResultStore_Local-S3.md) (5 shared connections)
- [SQLite Event Log & Projection](SQLite_Event_Log_%26_Projection.md) (5 shared connections)
- [Engine Ports & Adapters](Engine_Ports_%26_Adapters.md) (4 shared connections)
- [Local Stores & Deterministic Query](Local_Stores_%26_Deterministic_Query.md) (1 shared connections)
- [Detached Launcher Reconcile](Detached_Launcher_Reconcile.md) (1 shared connections)
- [CLI Run/Submit Commands](CLI_Run-Submit_Commands.md) (1 shared connections)
- [Event Observer Hook](Event_Observer_Hook.md) (1 shared connections)
- [Run Schedule Orchestration](Run_Schedule_Orchestration.md) (1 shared connections)

## Source Files

- `core/gherkai_core/adapters/result_store/__init__.py`
- `core/gherkai_core/adapters/result_store/local.py`
- `core/gherkai_core/persist.py`
- `core/tests/test_persist.py`

## Audit Trail

- EXTRACTED: 107 (88%)
- INFERRED: 14 (12%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*