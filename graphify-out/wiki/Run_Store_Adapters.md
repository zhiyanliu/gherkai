# Run Store Adapters

> 31 nodes · cohesion 0.09

## Key Concepts

- **LocalRunStore** (53 connections) — `core/gherkai_core/adapters/run_store/local.py`
- **.save_run()** (8 connections) — `core/gherkai_core/adapters/run_store/local.py`
- **._write_state()** (8 connections) — `core/gherkai_core/adapters/run_store/local.py`
- **.load_run_state()** (7 connections) — `core/gherkai_core/adapters/run_store/local.py`
- **._locked_rmw()** (7 connections) — `core/gherkai_core/adapters/run_store/local.py`
- **_atomic_write_json()** (6 connections) — `core/gherkai_core/adapters/run_store/local.py`
- **.finalize_run()** (6 connections) — `core/gherkai_core/adapters/run_store/local.py`
- **.update_job_state()** (6 connections) — `core/gherkai_core/adapters/run_store/local.py`
- **build_local_stores()** (6 connections) — `runtime/gherkai_runtime/compose.py`
- **.create_run()** (5 connections) — `core/gherkai_core/adapters/run_store/local.py`
- **.project_state()** (4 connections) — `core/gherkai_core/adapters/run_store/local.py`
- **.try_finalize()** (4 connections) — `core/gherkai_core/adapters/run_store/local.py`
- **run_store/__init__.py** (3 connections) — `core/gherkai_core/adapters/run_store/__init__.py`
- **.try_claim_job()** (3 connections) — `core/gherkai_core/adapters/run_store/local.py`
- **.__init__()** (2 connections) — `core/gherkai_core/adapters/run_store/local.py`
- **.preflight()** (2 connections) — `core/gherkai_core/adapters/run_store/local.py`
- **Path** (2 connections)
- **RunStore adapters（ADR 0016）：local（本包 `local.py`）+ DynamoDB（`ddb.py`，ADR 0030…** (1 connections) — `core/gherkai_core/adapters/run_store/__init__.py`
- **读回运行态（RunState）；不存在返回 None。** (1 connections) — `core/gherkai_core/adapters/run_store/local.py`
- **探活 no-op（ADR 0030 决定七）：本地文件后端无「表不存在」问题，目录随写随建。** (1 connections) — `core/gherkai_core/adapters/run_store/local.py`
- **在 run_state.json 上做跨进程原子 read-modify-write：持文件锁 → 读 state → mutate(state)→ (新…** (1 connections) — `core/gherkai_core/adapters/run_store/local.py`
- **CAS：仅当 jobs[scope_id] 当前 PENDING 才置 RUNNING（机制四）；随写 claimed_at（timeout 起算点）。** (1 connections) — `core/gherkai_core/adapters/run_store/local.py`
- **HWM 条件写 RunState：仅当传入 hwm ≥ 库中 hwm 才写（机制三①，挡 stale 覆盖）。 **run 级 status 钳为…** (1 connections) — `core/gherkai_core/adapters/run_store/local.py`
- **状态机单调条件写：仅当当前总 status 为非终态才写终态（机制三，commit 恰一次）。** (1 connections) — `core/gherkai_core/adapters/run_store/local.py`
- **控制面文件（run_meta.json / run_state.json）的原子写。 并发读者真实存在（ADR 0030 决定四/0034）：per-run…** (1 connections) — `core/gherkai_core/adapters/run_store/local.py`
- *... and 6 more nodes in this community*

## Relationships

- [Cloud Store Adapters](Cloud_Store_Adapters.md) (18 shared connections)
- [Run State Store](Run_State_Store.md) (12 shared connections)
- [Local Result Store](Local_Result_Store.md) (6 shared connections)
- [Job Domain Models](Job_Domain_Models.md) (5 shared connections)
- [Wall Clock Timestamps](Wall_Clock_Timestamps.md) (4 shared connections)
- [Local Detached Execution](Local_Detached_Execution.md) (3 shared connections)
- [Run Result Aggregation Tree](Run_Result_Aggregation_Tree.md) (3 shared connections)
- [Reconciler Orchestration](Reconciler_Orchestration.md) (2 shared connections)
- [Local Reconcile Loop Tests](Local_Reconcile_Loop_Tests.md) (2 shared connections)
- [Atomic Write and Report Stores](Atomic_Write_and_Report_Stores.md) (1 shared connections)
- [CLI Run Command Tests](CLI_Run_Command_Tests.md) (1 shared connections)
- [Worker Capability Queries](Worker_Capability_Queries.md) (1 shared connections)

## Source Files

- `core/gherkai_core/adapters/run_store/__init__.py`
- `core/gherkai_core/adapters/run_store/local.py`
- `runtime/gherkai_runtime/compose.py`

## Audit Trail

- EXTRACTED: 95 (92%)
- INFERRED: 8 (8%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*