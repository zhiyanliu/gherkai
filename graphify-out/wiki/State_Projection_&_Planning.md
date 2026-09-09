# State Projection & Planning

> 35 nodes · cohesion 0.12

## Key Concepts

- **test_project.py** (52 connections) — `core/tests/test_project.py`
- **ScopeStarted** (39 connections) — `core/gherkai_core/model.py`
- **_meta()** (28 connections) — `core/tests/test_project.py`
- **_passed_events()** (15 connections) — `core/tests/test_project.py`
- **plan_next()** (11 connections) — `core/gherkai_core/project.py`
- **_ev()** (10 connections) — `core/tests/test_project.py`
- **test_plan_next_finalize_when_all_terminal()** (8 connections) — `core/tests/test_project.py`
- **test_clean_exit_without_scope_done_is_error()** (7 connections) — `core/tests/test_project.py`
- **test_crash_no_scope_done_nonzero_exit_is_error()** (7 connections) — `core/tests/test_project.py`
- **test_error_clean_exit_incomplete_content_gets_attribution()** (7 connections) — `core/tests/test_project.py`
- **test_plan_next_not_finalize_while_running()** (7 connections) — `core/tests/test_project.py`
- **test_plan_next_respects_running_slots()** (7 connections) — `core/tests/test_project.py`
- **test_timed_out_exit_is_error_regardless_of_exit_code_shape()** (7 connections) — `core/tests/test_project.py`
- **test_hwm_is_max_worker_seq()** (6 connections) — `core/tests/test_project.py`
- **test_scope_started_running_without_exit()** (6 connections) — `core/tests/test_project.py`
- **test_timed_out_attribution_error_type_timeout()** (6 connections) — `core/tests/test_project.py`
- **test_two_things_present_clean_exit_terminal_passed()** (6 connections) — `core/tests/test_project.py`
- **test_plan_next_starts_up_to_concurrency()** (5 connections) — `core/tests/test_project.py`
- **test_scope_started_but_no_exit_is_running()** (5 connections) — `core/tests/test_project.py`
- **_timeout_exit()** (5 connections) — `core/tests/test_project.py`
- **据当前 RunState 提议下一步动作（ADR 0034 机制四，纯函数、无副作用）。 - 若所有 job 达终态（无 pending/running）→…** (1 connections) — `core/gherkai_core/project.py`
- **gherkai_core.project 纯投影测试（ADR 0034）：project(records)→RunState 的「两件都要」谓词 + HWM…** (1 connections) — `core/tests/test_project.py`
- **两件都要齐（scope_done ∧ exit=0）→ 终态取 scenario 归约（passed）。** (1 connections) — `core/tests/test_project.py`
- **超时处置的 stop → ERROR，不论 exit_code 形态（SIGKILL 137 / 协作退 0 / 未落值 None—— None 平时是保守…** (1 connections) — `core/tests/test_project.py`
- **归因 error_type="timeout"（对齐同步路径，[0031] 决定一）——即使内容完整（scope_done 都到了） 也以超时为根因、覆盖…** (1 connections) — `core/tests/test_project.py`
- *... and 10 more nodes in this community*

## Relationships

- [Event Replay Projection](Event_Replay_Projection.md) (48 shared connections)
- [Run Result Rendering](Run_Result_Rendering.md) (18 shared connections)
- [Event Progress Formatting](Event_Progress_Formatting.md) (11 shared connections)
- [Engine Ports & Adapters](Engine_Ports_%26_Adapters.md) (8 shared connections)
- [Local Result Store](Local_Result_Store.md) (5 shared connections)
- [Terminal Status Aggregation](Terminal_Status_Aggregation.md) (4 shared connections)
- [Conditional Write Tests](Conditional_Write_Tests.md) (3 shared connections)
- [Run State Rendering](Run_State_Rendering.md) (3 shared connections)
- [Boto Guard & S3 Offload](Boto_Guard_%26_S3_Offload.md) (3 shared connections)
- [Fargate Engine Tests](Fargate_Engine_Tests.md) (1 shared connections)
- [Run Scheduling Engine](Run_Scheduling_Engine.md) (1 shared connections)
- [Subprocess Engine Tests](Subprocess_Engine_Tests.md) (1 shared connections)

## Source Files

- `core/gherkai_core/model.py`
- `core/gherkai_core/project.py`
- `core/tests/test_project.py`

## Audit Trail

- EXTRACTED: 173 (94%)
- INFERRED: 12 (6%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*