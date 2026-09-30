# Run State Store

> 75 nodes · cohesion 0.05

## Key Concepts

- **RunState** (127 connections) — `core/gherkai_core/model.py`
- **DynamoDBRunStore** (40 connections) — `core/gherkai_core/adapters/run_store/ddb.py`
- **test_conditional_writes.py** (40 connections) — `core/tests/test_conditional_writes.py`
- **_meta()** (25 connections) — `core/tests/test_conditional_writes.py`
- **_initial()** (24 connections) — `core/tests/test_conditional_writes.py`
- **test_stale_projection_never_regresses_terminal_job_on_real_ddb()** (9 connections) — `core/tests/test_conditional_writes.py`
- **test_local_run_store_atomic.py** (9 connections) — `core/tests/test_local_run_store_atomic.py`
- **.create_run()** (8 connections) — `core/gherkai_core/adapters/run_store/ddb.py`
- **test_explain_cloud_not_landed_hint_carries_cloud_locator_flags()** (7 connections) — `cli/tests/test_main.py`
- **test_claim_is_exclusive_on_real_ddb()** (7 connections) — `core/tests/test_conditional_writes.py`
- **test_render_status_pending_run_with_claimed_job_does_not_hint()** (6 connections) — `cli/tests/test_main.py`
- **test_projection_never_lands_terminal_run_status()** (6 connections) — `core/tests/test_conditional_writes.py`
- **test_projection_with_unknown_scope_is_ignored_not_invented()** (6 connections) — `core/tests/test_conditional_writes.py`
- **test_same_hwm_terminal_job_not_regressed()** (6 connections) — `core/tests/test_conditional_writes.py`
- **test_stale_projection_rejected()** (6 connections) — `core/tests/test_conditional_writes.py`
- **.load_run_state()** (5 connections) — `core/gherkai_core/adapters/run_store/ddb.py`
- **.save_run()** (5 connections) — `core/gherkai_core/adapters/run_store/ddb.py`
- **run_store()** (5 connections) — `core/tests/test_conditional_writes.py`
- **test_equal_hwm_projection_allowed()** (5 connections) — `core/tests/test_conditional_writes.py`
- **test_projection_keeps_pending_while_no_job_started()** (5 connections) — `core/tests/test_conditional_writes.py`
- **test_projection_preserves_started_at()** (5 connections) — `core/tests/test_conditional_writes.py`
- **_state_scalars()** (4 connections) — `core/gherkai_core/adapters/run_store/ddb.py`
- **_real_run_id()** (4 connections) — `core/tests/test_conditional_writes.py`
- **_real_store()** (4 connections) — `core/tests/test_conditional_writes.py`
- **test_claim_nonexistent_job_fails()** (4 connections) — `core/tests/test_conditional_writes.py`
- *... and 50 more nodes in this community*

## Relationships

- [Job Domain Models](Job_Domain_Models.md) (47 shared connections)
- [Cloud Store Adapters](Cloud_Store_Adapters.md) (32 shared connections)
- [Run Result Aggregation Tree](Run_Result_Aggregation_Tree.md) (20 shared connections)
- [Event Log Adapters](Event_Log_Adapters.md) (18 shared connections)
- [Run Store Adapters](Run_Store_Adapters.md) (12 shared connections)
- [Cloud Integration Tests](Cloud_Integration_Tests.md) (9 shared connections)
- [Run State Projection](Run_State_Projection.md) (7 shared connections)
- [Reconciler Orchestration](Reconciler_Orchestration.md) (5 shared connections)
- [Wall Clock Timestamps](Wall_Clock_Timestamps.md) (5 shared connections)
- [S3 Store Adapters](S3_Store_Adapters.md) (4 shared connections)
- [Cloud Resource Preflight](Cloud_Resource_Preflight.md) (4 shared connections)
- [Run Status Rendering](Run_Status_Rendering.md) (3 shared connections)

## Source Files

- `cli/tests/test_main.py`
- `core/gherkai_core/adapters/run_store/ddb.py`
- `core/gherkai_core/model.py`
- `core/tests/test_conditional_writes.py`
- `core/tests/test_local_run_store_atomic.py`

## Audit Trail

- EXTRACTED: 285 (88%)
- INFERRED: 40 (12%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*