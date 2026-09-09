# Event Replay Projection

> 27 nodes · cohesion 0.10

## Key Concepts

- **project()** (43 connections) — `core/gherkai_core/project.py`
- **_exit()** (19 connections) — `core/tests/test_project.py`
- **test_clean_exit_without_events_converges_with_claimed_baseline()** (7 connections) — `core/tests/test_project.py`
- **test_exit_code_none_is_conservative_running()** (6 connections) — `core/tests/test_project.py`
- **test_hwm_across_scopes()** (6 connections) — `core/tests/test_project.py`
- **test_nonzero_exit_overrides_content_to_error()** (6 connections) — `core/tests/test_project.py`
- **test_out_of_order_records_reduced_by_seq()** (6 connections) — `core/tests/test_project.py`
- **test_sigkill_137_is_error()** (6 connections) — `core/tests/test_project.py`
- **test_clean_exit_without_any_event_is_error()** (5 connections) — `core/tests/test_project.py`
- **test_error_without_reduce_message_gets_default_attribution()** (5 connections) — `core/tests/test_project.py`
- **test_exit_none_without_events_is_running_grace()** (5 connections) — `core/tests/test_project.py`
- **test_network_exit_before_scope_started_is_error()** (5 connections) — `core/tests/test_project.py`
- **test_projected_run_status_ignores_aggregate_value_from_project()** (5 connections) — `core/tests/test_project.py`
- **test_no_records_job_is_pending()** (4 connections) — `core/tests/test_project.py`
- **从某 run 的**全量 events records** 纯推演出 RunState（ADR 0034 reconciler 核心，无 I/O）。…** (1 connections) — `core/gherkai_core/project.py`
- **关键（机制二）：scope_done 说 passed，但 exit_code!=0 → 判 ERROR（防"发完 scope_done 又非0退出"误报）。** (1 connections) — `core/tests/test_project.py`
- **SIGKILL 截断 exit=137 → ERROR（实测 payload 带 137，机制二）。** (1 connections) — `core/tests/test_project.py`
- **exit_code=None（宽限态未落值）→ 保守判 RUNNING、不轻易落终态（机制二兜底）。** (1 connections) — `core/tests/test_project.py`
- **worker 起来即崩（非 0 退出、零事件）→ message 不再全空——补默认归因指向 worker 日志 （detached 真跑教训：error…** (1 connections) — `core/tests/test_project.py`
- **多 scope：HWM 取跨 scope 的全局 max。** (1 connections) — `core/tests/test_project.py`
- **乱序 records（全量重放抗乱序，机制三前提）：project 内按 seq 升序归约，结果与顺序无关。** (1 connections) — `core/tests/test_project.py`
- **判据只看 job 态：project() 的 run 级 status 是终态聚合值（零事件的全 pending run 也吐 PASSED）， 喂它的…** (1 connections) — `core/tests/test_project.py`
- **零事件 + exit==0（构造期 SIGTERM 干净退出，0024 设计内）→ ERROR，不得判 PENDING。 若判 PENDING：与已…** (1 connections) — `core/tests/test_project.py`
- **同上,带「已 claim RUNNING」基线也必须收敛到 ERROR(终态 rank > running,单调合并不回退)。** (1 connections) — `core/tests/test_project.py`
- **零事件 + exit=None（TaskFailedToStart 的 STOPPED 无 exitCode）→ RUNNING 宽限（等观察者补），非…** (1 connections) — `core/tests/test_project.py`
- *... and 2 more nodes in this community*

## Relationships

- [State Projection & Planning](State_Projection_%26_Planning.md) (48 shared connections)
- [Run Result Rendering](Run_Result_Rendering.md) (8 shared connections)
- [Run State Rendering](Run_State_Rendering.md) (4 shared connections)
- [Conditional Write Tests](Conditional_Write_Tests.md) (4 shared connections)
- [Cloud Launcher & DDB Event Log](Cloud_Launcher_%26_DDB_Event_Log.md) (3 shared connections)
- [Boto Guard & S3 Offload](Boto_Guard_%26_S3_Offload.md) (2 shared connections)
- [SQLite Event Log](SQLite_Event_Log.md) (2 shared connections)
- [Terminal Status Aggregation](Terminal_Status_Aggregation.md) (1 shared connections)
- [Engine Ports & Adapters](Engine_Ports_%26_Adapters.md) (1 shared connections)

## Source Files

- `core/gherkai_core/project.py`
- `core/tests/test_project.py`

## Audit Trail

- EXTRACTED: 107 (100%)
- INFERRED: 0 (0%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*