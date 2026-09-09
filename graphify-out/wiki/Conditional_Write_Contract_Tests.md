# Conditional Write Contract Tests

> 37 nodes · cohesion 0.10

## Key Concepts

- **test_conditional_writes.py** (34 connections) — `core/tests/test_conditional_writes.py`
- **_meta()** (21 connections) — `core/tests/test_conditional_writes.py`
- **_initial()** (20 connections) — `core/tests/test_conditional_writes.py`
- **test_projection_lands_running_once_any_job_advanced()** (7 connections) — `core/tests/test_conditional_writes.py`
- **test_projection_preserves_claimed_at()** (7 connections) — `core/tests/test_conditional_writes.py`
- **test_projection_never_lands_terminal_run_status()** (6 connections) — `core/tests/test_conditional_writes.py`
- **test_same_hwm_terminal_job_not_regressed()** (6 connections) — `core/tests/test_conditional_writes.py`
- **test_stale_projection_rejected()** (6 connections) — `core/tests/test_conditional_writes.py`
- **test_equal_hwm_projection_allowed()** (5 connections) — `core/tests/test_conditional_writes.py`
- **test_projection_keeps_pending_while_no_job_started()** (5 connections) — `core/tests/test_conditional_writes.py`
- **test_projection_preserves_started_at()** (5 connections) — `core/tests/test_conditional_writes.py`
- **test_claim_nonexistent_job_fails()** (4 connections) — `core/tests/test_conditional_writes.py`
- **test_claim_pending_succeeds_once()** (4 connections) — `core/tests/test_conditional_writes.py`
- **test_claim_two_different_jobs_both_succeed()** (4 connections) — `core/tests/test_conditional_writes.py`
- **test_claim_writes_claimed_at()** (4 connections) — `core/tests/test_conditional_writes.py`
- **test_claimed_running_not_regressed_to_pending_same_hwm()** (4 connections) — `core/tests/test_conditional_writes.py`
- **test_double_finalize_rejected()** (4 connections) — `core/tests/test_conditional_writes.py`
- **test_finalize_from_nonterminal_succeeds()** (4 connections) — `core/tests/test_conditional_writes.py`
- **test_project_advances_hwm()** (4 connections) — `core/tests/test_conditional_writes.py`
- **test_finalize_missing_run_fails()** (2 connections) — `core/tests/test_conditional_writes.py`
- **RunStore 无状态跑批条件写对拍测试（ADR 0034 P2）：try_claim_job / project_state /…** (1 connections) — `core/tests/test_conditional_writes.py`
- **关键（机制三）：先写 hwm=10，再用 stale 快照 hwm=5 投影 → 被挡（False），不覆盖。** (1 connections) — `core/tests/test_conditional_writes.py`
- **同 hwm 投影写允许（幂等：同一批 events 重放算出同 state，覆盖无害）。** (1 connections) — `core/tests/test_conditional_writes.py`
- **关键（机制三②，ADR 0034）：task_exited 无数值 seq → 两投影同 HWM，job 终态不得被 stale 投影刷回。…** (1 connections) — `core/tests/test_conditional_writes.py`
- **机制四护栏：已 CAS claim 的 RUNNING 不被同 HWM 的 pending 视图投影刷回（防 double-launch 窗口重开）。** (1 connections) — `core/tests/test_conditional_writes.py`
- *... and 12 more nodes in this community*

## Relationships

- [Run State Rendering & Boto Guard](Run_State_Rendering_%26_Boto_Guard.md) (11 shared connections)
- [SQLite Event Log & Projection](SQLite_Event_Log_%26_Projection.md) (10 shared connections)
- [DynamoDB RunStore Conditional Writes](DynamoDB_RunStore_Conditional_Writes.md) (8 shared connections)
- [Engine Ports & Adapters](Engine_Ports_%26_Adapters.md) (7 shared connections)
- [Run Result Verdict Model](Run_Result_Verdict_Model.md) (1 shared connections)

## Source Files

- `core/tests/test_conditional_writes.py`

## Audit Trail

- EXTRACTED: 105 (100%)
- INFERRED: 0 (0%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*