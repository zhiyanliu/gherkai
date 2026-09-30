# Conditional Write Tests

> 49 nodes · cohesion 0.08

## Key Concepts

- **test_conditional_writes.py** (40 connections) — `core/tests/test_conditional_writes.py`
- **_meta()** (25 connections) — `core/tests/test_conditional_writes.py`
- **_initial()** (24 connections) — `core/tests/test_conditional_writes.py`
- **test_stale_projection_never_regresses_terminal_job_on_real_ddb()** (9 connections) — `core/tests/test_conditional_writes.py`
- **test_claim_is_exclusive_on_real_ddb()** (7 connections) — `core/tests/test_conditional_writes.py`
- **test_projection_lands_running_once_any_job_advanced()** (7 connections) — `core/tests/test_conditional_writes.py`
- **test_projection_preserves_claimed_at()** (7 connections) — `core/tests/test_conditional_writes.py`
- **test_projection_without_baseline_keeps_stored_lineage()** (7 connections) — `core/tests/test_conditional_writes.py`
- **test_projection_never_lands_terminal_run_status()** (6 connections) — `core/tests/test_conditional_writes.py`
- **test_projection_with_unknown_scope_is_ignored_not_invented()** (6 connections) — `core/tests/test_conditional_writes.py`
- **test_same_hwm_terminal_job_not_regressed()** (6 connections) — `core/tests/test_conditional_writes.py`
- **test_stale_projection_rejected()** (6 connections) — `core/tests/test_conditional_writes.py`
- **test_equal_hwm_projection_allowed()** (5 connections) — `core/tests/test_conditional_writes.py`
- **test_projection_keeps_pending_while_no_job_started()** (5 connections) — `core/tests/test_conditional_writes.py`
- **test_projection_preserves_started_at()** (5 connections) — `core/tests/test_conditional_writes.py`
- **_real_run_id()** (4 connections) — `core/tests/test_conditional_writes.py`
- **_real_store()** (4 connections) — `core/tests/test_conditional_writes.py`
- **test_claim_nonexistent_job_fails()** (4 connections) — `core/tests/test_conditional_writes.py`
- **test_claim_pending_succeeds_once()** (4 connections) — `core/tests/test_conditional_writes.py`
- **test_claim_two_different_jobs_both_succeed()** (4 connections) — `core/tests/test_conditional_writes.py`
- **test_claim_writes_claimed_at()** (4 connections) — `core/tests/test_conditional_writes.py`
- **test_claimed_running_not_regressed_to_pending_same_hwm()** (4 connections) — `core/tests/test_conditional_writes.py`
- **test_double_finalize_rejected()** (4 connections) — `core/tests/test_conditional_writes.py`
- **test_finalize_from_nonterminal_succeeds()** (4 connections) — `core/tests/test_conditional_writes.py`
- **test_project_advances_hwm()** (4 connections) — `core/tests/test_conditional_writes.py`
- *... and 24 more nodes in this community*

## Relationships

- [Run State Rendering](Run_State_Rendering.md) (12 shared connections)
- [DynamoDB Run Store](DynamoDB_Run_Store.md) (9 shared connections)
- [Run Definition Domain Model](Run_Definition_Domain_Model.md) (9 shared connections)
- [Event Records Projection](Event_Records_Projection.md) (8 shared connections)
- [State Projection Tests](State_Projection_Tests.md) (5 shared connections)
- [Result Tree Text Rendering](Result_Tree_Text_Rendering.md) (1 shared connections)
- [Core Adapters Documentation](Core_Adapters_Documentation.md) (1 shared connections)

## Source Files

- `core/tests/test_conditional_writes.py`

## Audit Trail

- EXTRACTED: 138 (100%)
- INFERRED: 0 (0%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*