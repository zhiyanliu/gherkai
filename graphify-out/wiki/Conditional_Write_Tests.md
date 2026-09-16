# Conditional Write Tests

> 43 nodes · cohesion 0.09

## Key Concepts

- **test_conditional_writes.py** (36 connections) — `core/tests/test_conditional_writes.py`
- **_meta()** (23 connections) — `core/tests/test_conditional_writes.py`
- **_initial()** (22 connections) — `core/tests/test_conditional_writes.py`
- **test_projection_lands_running_once_any_job_advanced()** (7 connections) — `core/tests/test_conditional_writes.py`
- **test_projection_preserves_claimed_at()** (7 connections) — `core/tests/test_conditional_writes.py`
- **test_projection_without_baseline_keeps_stored_lineage()** (7 connections) — `core/tests/test_conditional_writes.py`
- **test_projection_never_lands_terminal_run_status()** (6 connections) — `core/tests/test_conditional_writes.py`
- **test_projection_with_unknown_scope_is_ignored_not_invented()** (6 connections) — `core/tests/test_conditional_writes.py`
- **test_same_hwm_terminal_job_not_regressed()** (6 connections) — `core/tests/test_conditional_writes.py`
- **test_stale_projection_rejected()** (6 connections) — `core/tests/test_conditional_writes.py`
- **run_store()** (5 connections) — `core/tests/test_conditional_writes.py`
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
- *... and 18 more nodes in this community*

## Relationships

- [Run State Projection](Run_State_Projection.md) (13 shared connections)
- [Job Explain & S3 Offload](Job_Explain_%26_S3_Offload.md) (11 shared connections)
- [Run State Rendering](Run_State_Rendering.md) (9 shared connections)
- [DynamoDB RunStore Adapter](DynamoDB_RunStore_Adapter.md) (8 shared connections)
- [Cloud Boto3 Guards & EventLog](Cloud_Boto3_Guards_%26_EventLog.md) (2 shared connections)
- [AWS Test Fixtures](AWS_Test_Fixtures.md) (1 shared connections)

## Source Files

- `core/tests/test_conditional_writes.py`

## Audit Trail

- EXTRACTED: 122 (100%)
- INFERRED: 0 (0%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*