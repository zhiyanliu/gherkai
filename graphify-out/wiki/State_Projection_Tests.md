# State Projection Tests

> 19 nodes · cohesion 0.14

## Key Concepts

- **project()** (44 connections) — `core/gherkai_core/project.py`
- **_passed_events()** (16 connections) — `core/tests/test_project.py`
- **test_hwm_across_scopes()** (6 connections) — `core/tests/test_project.py`
- **test_hwm_is_max_worker_seq()** (6 connections) — `core/tests/test_project.py`
- **test_nonzero_exit_overrides_content_to_error()** (6 connections) — `core/tests/test_project.py`
- **test_out_of_order_records_reduced_by_seq()** (6 connections) — `core/tests/test_project.py`
- **test_sigkill_137_is_error()** (6 connections) — `core/tests/test_project.py`
- **test_two_things_present_clean_exit_terminal_passed()** (6 connections) — `core/tests/test_project.py`
- **test_scope_started_but_no_exit_is_running()** (5 connections) — `core/tests/test_project.py`
- **test_no_records_job_is_pending()** (4 connections) — `core/tests/test_project.py`
- **从某 run 的**全量 events records** 纯推演出 RunState（ADR 0034 reconciler 核心，无 I/O）。…** (1 connections) — `core/gherkai_core/project.py`
- **两件都要齐（scope_done 与 exit=0 都齐）→ 终态取 scenario 归约（passed）。** (1 connections) — `core/tests/test_project.py`
- **关键（机制二）：scope_done 说 passed，但 exit_code!=0 → 判 ERROR（防"发完 scope_done 又非0退出"误报）。** (1 connections) — `core/tests/test_project.py`
- **SIGKILL 截断 exit=137 → ERROR（实测 payload 带 137，机制二）。** (1 connections) — `core/tests/test_project.py`
- **high_water_mark 是所有 scope 的 worker 段 max seq（exit 记录无 seq、不参与）。** (1 connections) — `core/tests/test_project.py`
- **多 scope：HWM 取跨 scope 的全局 max。** (1 connections) — `core/tests/test_project.py`
- **乱序 records（全量重放抗乱序，机制三前提）：project 内按 seq 升序归约，结果与顺序无关。** (1 connections) — `core/tests/test_project.py`
- **definition 里的 job 没有任何 record → PENDING（还没起）。** (1 connections) — `core/tests/test_project.py`
- **见了 scope_started、有 scope_done，但没 task_exit → RUNNING（进程未确认终止，两件缺一）。** (1 connections) — `core/tests/test_project.py`

## Relationships

- [Event Records Projection](Event_Records_Projection.md) (41 shared connections)
- [Conditional Write Tests](Conditional_Write_Tests.md) (5 shared connections)
- [Result Tree Text Rendering](Result_Tree_Text_Rendering.md) (3 shared connections)
- [Cloud Launcher and EventLog](Cloud_Launcher_and_EventLog.md) (3 shared connections)
- [Reconciler Plan Next](Reconciler_Plan_Next.md) (3 shared connections)
- [Run State Rendering](Run_State_Rendering.md) (2 shared connections)
- [Run Definition Domain Model](Run_Definition_Domain_Model.md) (2 shared connections)
- [Worker Log Event Formatting](Worker_Log_Event_Formatting.md) (2 shared connections)
- [DynamoDB Run Store](DynamoDB_Run_Store.md) (1 shared connections)
- [Reconcile Tick and Report](Reconcile_Tick_and_Report.md) (1 shared connections)
- [Projected Run Status](Projected_Run_Status.md) (1 shared connections)
- [Core Adapters Documentation](Core_Adapters_Documentation.md) (1 shared connections)

## Source Files

- `core/gherkai_core/project.py`
- `core/tests/test_project.py`

## Audit Trail

- EXTRACTED: 90 (100%)
- INFERRED: 0 (0%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*