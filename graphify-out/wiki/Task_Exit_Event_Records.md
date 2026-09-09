# Task Exit Event Records

> 7 nodes · cohesion 0.29

## Key Concepts

- **events_pk()** (14 connections) — `core/gherkai_core/adapters/fargate_engine.py`
- **.has_exit()** (3 connections) — `core/gherkai_core/adapters/event_log/ddb.py`
- **.record_exit()** (3 connections) — `core/gherkai_core/adapters/event_log/ddb.py`
- **test_events_pk_composite_run_id_scope_id()** (2 connections) — `core/tests/test_fargate_engine.py`
- **退出观察者 Lambda 调：写 task_exited 到保留高位 SK（独立键空间，机制一）。INSERT 幂等（覆盖同键）。…** (1 connections) — `core/gherkai_core/adapters/event_log/ddb.py`
- **单个 scope 有没有退出记录（**只读**，退出记录键位确定 → 单 item 点查、不走 records() 重放整 run）。…** (1 connections) — `core/gherkai_core/adapters/event_log/ddb.py`
- **events 表分区键 = run_id#scope_id（复合，防重复跑撞键）。worker/adapter 各自本地拼、须逐字一致。** (1 connections) — `core/gherkai_core/adapters/fargate_engine.py`

## Relationships

- [Cloud Launcher & DDB Event Log](Cloud_Launcher_%26_DDB_Event_Log.md) (5 shared connections)
- [Fargate Engine Tests](Fargate_Engine_Tests.md) (4 shared connections)
- [Run Result Rendering](Run_Result_Rendering.md) (2 shared connections)
- [Fargate Engine](Fargate_Engine.md) (1 shared connections)
- [Engine Ports & Adapters](Engine_Ports_%26_Adapters.md) (1 shared connections)

## Source Files

- `core/gherkai_core/adapters/event_log/ddb.py`
- `core/gherkai_core/adapters/fargate_engine.py`
- `core/tests/test_fargate_engine.py`

## Audit Trail

- EXTRACTED: 19 (100%)
- INFERRED: 0 (0%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*