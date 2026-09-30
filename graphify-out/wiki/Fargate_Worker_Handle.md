# Fargate Worker Handle

> 13 nodes · cohesion 0.15

## Key Concepts

- **_FakeEcs** (15 connections) — `core/tests/test_fargate_engine.py`
- **_SeqEcs** (15 connections) — `core/tests/test_fargate_engine.py`
- **FargateWorkerHandle** (12 connections) — `core/gherkai_core/adapters/fargate_engine.py`
- **.stop()** (2 connections) — `core/gherkai_core/adapters/fargate_engine.py`
- **.__init__()** (1 connections) — `core/gherkai_core/adapters/fargate_engine.py`
- **一个正在运行的 Fargate task 的句柄。stop() 翻成 StopTask（ADR 0026 机制层，对称…** (1 connections) — `core/gherkai_core/adapters/fargate_engine.py`
- **请求优雅停止即调 StopTask。 **grace_period_s 在 Fargate 上无法逐次传**（ADR 0024/0032）：容器…** (1 connections) — `core/gherkai_core/adapters/fargate_engine.py`
- **.describe_tasks()** (1 connections) — `core/tests/test_fargate_engine.py`
- **.__init__()** (1 connections) — `core/tests/test_fargate_engine.py`
- **构造 describe_tasks 响应的假 ecs client（moto exitCode 恒 0、lastStatus 由 describe…** (1 connections) — `core/tests/test_fargate_engine.py`
- **按序返回 describe_tasks 响应的假 ecs（模拟 STOPPED 翻转后 exitCode 落值时序）。** (1 connections) — `core/tests/test_fargate_engine.py`
- **.describe_tasks()** (1 connections) — `core/tests/test_fargate_engine.py`
- **.__init__()** (1 connections) — `core/tests/test_fargate_engine.py`

## Relationships

- [Job Domain Models](Job_Domain_Models.md) (8 shared connections)
- [Fargate Engine Tests](Fargate_Engine_Tests.md) (5 shared connections)
- [Fargate Engine Adapter](Fargate_Engine_Adapter.md) (3 shared connections)
- [Event Log Adapters](Event_Log_Adapters.md) (3 shared connections)
- [Event Gap & ECS Polling](Event_Gap_%26_ECS_Polling.md) (2 shared connections)
- [Typed Errors and Wire Protocol](Typed_Errors_and_Wire_Protocol.md) (2 shared connections)
- [Run State Projection](Run_State_Projection.md) (2 shared connections)
- [Run Result Aggregation Tree](Run_Result_Aggregation_Tree.md) (2 shared connections)
- [Event Formatting](Event_Formatting.md) (2 shared connections)

## Source Files

- `core/gherkai_core/adapters/fargate_engine.py`
- `core/tests/test_fargate_engine.py`

## Audit Trail

- EXTRACTED: 17 (41%)
- INFERRED: 24 (59%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*