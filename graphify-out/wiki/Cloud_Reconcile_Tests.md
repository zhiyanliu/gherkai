# Cloud Reconcile Tests

> 22 nodes · cohesion 0.16

## Key Concepts

- **test_cloud_reconcile.py** (38 connections) — `core/tests/test_cloud_reconcile.py`
- **DdbEventLog** (25 connections) — `core/gherkai_core/adapters/event_log/ddb.py`
- **test_tick_with_ddb_backend()** (10 connections) — `core/tests/test_cloud_reconcile.py`
- **_passed_worker_events()** (8 connections) — `core/tests/test_cloud_reconcile.py`
- **_meta()** (6 connections) — `core/tests/test_cloud_reconcile.py`
- **test_ddb_multi_scope_records()** (6 connections) — `core/tests/test_cloud_reconcile.py`
- **test_ddb_records_feed_project()** (6 connections) — `core/tests/test_cloud_reconcile.py`
- **test_ddb_record_exit_independent_keyspace()** (5 connections) — `core/tests/test_cloud_reconcile.py`
- **_put_worker_event()** (4 connections) — `core/tests/test_cloud_reconcile.py`
- **test_ddb_has_exit_single_scope()** (4 connections) — `core/tests/test_cloud_reconcile.py`
- **test_ddb_event_log_queries_with_consistent_read()** (3 connections) — `core/tests/test_cloud_reconcile.py`
- **test_ddb_event_log_reads_worker_events()** (3 connections) — `core/tests/test_cloud_reconcile.py`
- **.__init__()** (2 connections) — `core/gherkai_core/adapters/event_log/ddb.py`
- **cloud EventLog：从 events 表读全量重放（逐 scope Query）+ 写 task_exited（保留高位 SK）。…** (1 connections) — `core/gherkai_core/adapters/event_log/ddb.py`
- **cloud 无状态批量运行 core 侧测试（ADR 0034 云端后端）：DdbEventLog + CloudLauncher +…** (1 connections) — `core/tests/test_cloud_reconcile.py`
- **多 scope：逐 scope Query 拼全量（不需 GSI）。** (1 connections) — `core/tests/test_cloud_reconcile.py`
- **reconcile.tick 用 DdbEventLog + DynamoDBRunStore + CloudLauncher（fake…** (1 connections) — `core/tests/test_cloud_reconcile.py`
- **records() 是 reconcile 的投影输入：finalize 前 _final_drain / 退出观察者刚写的尾事件必须**立即**可读…** (1 connections) — `core/tests/test_cloud_reconcile.py`
- **模拟 worker PutItem 一条执行事件（含 expires_at=emit_ts+7d，DdbEventLog 据此还原 emit_ts）。** (1 connections) — `core/tests/test_cloud_reconcile.py`
- **task_exited 写保留高位 SK（机制一独立键空间），records() 里 kind='exit'、不占 worker seq 段。** (1 connections) — `core/tests/test_cloud_reconcile.py`
- **has_exit 只看本 scope 的退出记录（超时处置的「已在即让路」判据，不重放整 run）：有退出记录才 True， 只有 worker 事件的…** (1 connections) — `core/tests/test_cloud_reconcile.py`
- **DdbEventLog.records() → project() 推正确终态（两件都要齐 → passed）。** (1 connections) — `core/tests/test_cloud_reconcile.py`

## Relationships

- [Cloud Launcher](Cloud_Launcher.md) (11 shared connections)
- [Job Domain Models](Job_Domain_Models.md) (10 shared connections)
- [DynamoDB Event Log](DynamoDB_Event_Log.md) (9 shared connections)
- [Event Log Adapters](Event_Log_Adapters.md) (6 shared connections)
- [Run State Projection](Run_State_Projection.md) (3 shared connections)
- [Cloud Store Adapters](Cloud_Store_Adapters.md) (2 shared connections)
- [Run State Store](Run_State_Store.md) (2 shared connections)
- [Reconciler Orchestration](Reconciler_Orchestration.md) (2 shared connections)
- [Cloud Event Drain Tests](Cloud_Event_Drain_Tests.md) (1 shared connections)
- [Fargate Engine Tests](Fargate_Engine_Tests.md) (1 shared connections)
- [Exit Observer Lambda](Exit_Observer_Lambda.md) (1 shared connections)
- [Reconciler Lambda](Reconciler_Lambda.md) (1 shared connections)

## Source Files

- `core/gherkai_core/adapters/event_log/ddb.py`
- `core/tests/test_cloud_reconcile.py`

## Audit Trail

- EXTRACTED: 84 (92%)
- INFERRED: 7 (8%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*