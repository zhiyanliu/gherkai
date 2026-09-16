# Run State Rendering

> 27 nodes · cohesion 0.08

## Key Concepts

- **RunState** (125 connections) — `core/gherkai_core/model.py`
- **WorkerHandle** (12 connections) — `core/gherkai_core/ports.py`
- **_mk_state()** (9 connections) — `cli/tests/test_main.py`
- **test_explain_cloud_not_landed_hint_carries_cloud_locator_flags()** (7 connections) — `cli/tests/test_main.py`
- **render_run_state()** (6 connections) — `cli/gherkai_cli/render.py`
- **test_render_status_pending_run_with_claimed_job_does_not_hint()** (6 connections) — `cli/tests/test_main.py`
- **.load_run_state()** (5 connections) — `core/gherkai_core/adapters/run_store/ddb.py`
- **.project_state()** (5 connections) — `core/gherkai_core/adapters/run_store/ddb.py`
- **.create_run()** (5 connections) — `core/gherkai_core/adapters/run_store/local.py`
- **.begin()** (5 connections) — `core/gherkai_core/persist.py`
- **test_render_run_state_lists_jobs_and_session_lineage()** (4 connections) — `cli/tests/test_render.py`
- **test_render_run_state_shows_ended_at_when_terminal()** (4 connections) — `cli/tests/test_render.py`
- **_state_scalars()** (4 connections) — `core/gherkai_core/adapters/run_store/ddb.py`
- **.create_run()** (3 connections) — `core/gherkai_core/ports.py`
- **.save_run()** (3 connections) — `core/gherkai_core/ports.py`
- **.stop()** (2 connections) — `core/gherkai_core/ports.py`
- **`status` 的 RunState 人读渲染（轻量；权威判定明细读 jobs/*.json 或 --json）。 local/cloud…** (1 connections) — `cli/gherkai_cli/render.py`
- **run 级仍 pending 但已有 job 被 claim（running）→ 推进已开始，不提示「可能未启动」。这是 detached 的正常窗口：…** (1 connections) — `cli/tests/test_main.py`
- **cloud 档「判定明细尚未落地」给的 status 命令必带 --backend cloud --prefix：照抄要跑得通， 否则落回 local…** (1 connections) — `cli/tests/test_main.py`
- **HWM 条件写 STATE：仅当 (传入 hwm ≥ 库中 hwm) 且 (库中未 finalize) 才写（机制三①）。CCF → stale/已终态 →…** (1 connections) — `core/gherkai_core/adapters/run_store/ddb.py`
- **读回运行态（从 STATE item，jobs 原生 Map → dict[scope_id, JobState]）；不存在返回 None。…** (1 connections) — `core/gherkai_core/adapters/run_store/ddb.py`
- **RunState 顶层标量 → DDB 属性（status + omit-when-None 的起止 + hwm，对齐…** (1 connections) — `core/gherkai_core/adapters/run_store/ddb.py`
- **run 开始：写 definition（run_meta.json）+ 初始运行态（run_state.json，各 job 一般为 pending）。…** (1 connections) — `core/gherkai_core/adapters/run_store/local.py`
- **一次 run 的**控制面运行态**（status/血缘/起止；执行后产生，ADR 0016 控制面）。 与…** (1 connections) — `core/gherkai_core/model.py`
- **run 开始（schedule 之前）：先探活三个 store，再写 definition + 初始全 pending 运行态。 满足 ADR…** (1 connections) — `core/gherkai_core/persist.py`
- *... and 2 more nodes in this community*

## Relationships

- [Job Explain & S3 Offload](Job_Explain_%26_S3_Offload.md) (33 shared connections)
- [DynamoDB RunStore Adapter](DynamoDB_RunStore_Adapter.md) (32 shared connections)
- [Cloud Boto3 Guards & EventLog](Cloud_Boto3_Guards_%26_EventLog.md) (11 shared connections)
- [Run Status Rendering](Run_Status_Rendering.md) (9 shared connections)
- [Conditional Write Tests](Conditional_Write_Tests.md) (9 shared connections)
- [S3 Report Store & Control Plane](S3_Report_Store_%26_Control_Plane.md) (8 shared connections)
- [Cloud Adapter Integration Tests](Cloud_Adapter_Integration_Tests.md) (7 shared connections)
- [Run State Projection](Run_State_Projection.md) (6 shared connections)
- [SQLite Event Log](SQLite_Event_Log.md) (6 shared connections)
- [Reconciler Ports](Reconciler_Ports.md) (5 shared connections)
- [Event Formatting](Event_Formatting.md) (5 shared connections)
- [Cloud Job Launcher](Cloud_Job_Launcher.md) (4 shared connections)

## Source Files

- `cli/gherkai_cli/render.py`
- `cli/tests/test_main.py`
- `cli/tests/test_render.py`
- `core/gherkai_core/adapters/run_store/ddb.py`
- `core/gherkai_core/adapters/run_store/local.py`
- `core/gherkai_core/model.py`
- `core/gherkai_core/persist.py`
- `core/gherkai_core/ports.py`

## Audit Trail

- EXTRACTED: 150 (80%)
- INFERRED: 38 (20%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*