# Event Exit Records & Keys

> 7 nodes · cohesion 0.29

## Key Concepts

- **events_pk()** (15 connections) — `core/gherkai_core/adapters/fargate_engine.py`
- **.has_exit()** (3 connections) — `core/gherkai_core/adapters/event_log/ddb.py`
- **.record_exit()** (3 connections) — `core/gherkai_core/adapters/event_log/ddb.py`
- **test_events_pk_composite_run_id_scope_id()** (2 connections) — `core/tests/test_fargate_engine.py`
- **单个 scope 有没有退出记录（**只读**，退出记录键位确定 → 单 item 点查、不走 records() 重放整 run）。…** (1 connections) — `core/gherkai_core/adapters/event_log/ddb.py`
- **退出观察者 Lambda 调：写 task_exited 到保留高位 SK（独立键空间，机制一）。INSERT 幂等（覆盖同键）。…** (1 connections) — `core/gherkai_core/adapters/event_log/ddb.py`
- **events 表分区键为 `run_id#scope_id`（复合，防重复运行撞键）。worker/adapter 各自本地拼、须逐字一致。** (1 connections) — `core/gherkai_core/adapters/fargate_engine.py`

## Relationships

- [Cloud Launcher Reconcile Tests](Cloud_Launcher_Reconcile_Tests.md) (6 shared connections)
- [Worker Exit Drain Tests](Worker_Exit_Drain_Tests.md) (2 shared connections)
- [Cloud Adapter Boundary Modules](Cloud_Adapter_Boundary_Modules.md) (2 shared connections)
- [Fargate Engine Tests](Fargate_Engine_Tests.md) (2 shared connections)
- [Event Wire Protocol](Event_Wire_Protocol.md) (1 shared connections)
- [Fargate Engine Adapter](Fargate_Engine_Adapter.md) (1 shared connections)

## Source Files

- `core/gherkai_core/adapters/event_log/ddb.py`
- `core/gherkai_core/adapters/fargate_engine.py`
- `core/tests/test_fargate_engine.py`

## Audit Trail

- EXTRACTED: 20 (100%)
- INFERRED: 0 (0%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*