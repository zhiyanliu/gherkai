# DynamoDB Event Log

> 13 nodes · cohesion 0.15

## Key Concepts

- **events_pk()** (15 connections) — `core/gherkai_core/adapters/fargate_engine.py`
- **.records()** (7 connections) — `core/gherkai_core/adapters/event_log/ddb.py`
- **test_ddb_record_exit_reason_roundtrip()** (4 connections) — `core/tests/test_cloud_reconcile.py`
- **._emit_ts()** (3 connections) — `core/gherkai_core/adapters/event_log/ddb.py`
- **.has_exit()** (3 connections) — `core/gherkai_core/adapters/event_log/ddb.py`
- **.record_exit()** (3 connections) — `core/gherkai_core/adapters/event_log/ddb.py`
- **test_events_pk_composite_run_id_scope_id()** (2 connections) — `core/tests/test_fargate_engine.py`
- **单个 scope 有没有退出记录（**只读**，退出记录键位确定 → 单 item 点查、不走 records() 重放整 run）。…** (1 connections) — `core/gherkai_core/adapters/event_log/ddb.py`
- **退出观察者 Lambda 调：写 task_exited 到保留高位 SK（独立键空间，机制一）。INSERT 幂等（覆盖同键）。…** (1 connections) — `core/gherkai_core/adapters/event_log/ddb.py`
- **读某 run 全量 records（逐 scope Query worker 段 events + 取 task_exited）→ 供 project…** (1 connections) — `core/gherkai_core/adapters/event_log/ddb.py`
- **从 events item 还原 worker emit 墙钟（reduce_event 的 now，供算时长）。 写端（worker EventSink）写…** (1 connections) — `core/gherkai_core/adapters/event_log/ddb.py`
- **events 表分区键为 `run_id#scope_id`（复合，防重复运行撞键）。worker/adapter 各自本地拼、须逐字一致。** (1 connections) — `core/gherkai_core/adapters/fargate_engine.py`
- **DDB 侧 reason 属性 omit-when-empty、records() 读回进 TaskExited.reason（观察者落哨兵时的用户可见归因）。** (1 connections) — `core/tests/test_cloud_reconcile.py`

## Relationships

- [Cloud Reconcile Tests](Cloud_Reconcile_Tests.md) (9 shared connections)
- [Event Log Adapters](Event_Log_Adapters.md) (3 shared connections)
- [Cloud Event Drain Tests](Cloud_Event_Drain_Tests.md) (2 shared connections)
- [Fargate Engine Tests](Fargate_Engine_Tests.md) (2 shared connections)
- [Typed Errors and Wire Protocol](Typed_Errors_and_Wire_Protocol.md) (1 shared connections)
- [Fargate Engine Adapter](Fargate_Engine_Adapter.md) (1 shared connections)
- [Job Domain Models](Job_Domain_Models.md) (1 shared connections)

## Source Files

- `core/gherkai_core/adapters/event_log/ddb.py`
- `core/gherkai_core/adapters/fargate_engine.py`
- `core/tests/test_cloud_reconcile.py`
- `core/tests/test_fargate_engine.py`

## Audit Trail

- EXTRACTED: 31 (100%)
- INFERRED: 0 (0%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*