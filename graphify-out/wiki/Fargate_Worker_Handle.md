# Fargate Worker Handle

> 9 nodes · cohesion 0.22

## Key Concepts

- **_SeqEcs** (15 connections) — `core/tests/test_fargate_engine.py`
- **FargateWorkerHandle** (12 connections) — `core/gherkai_core/adapters/fargate_engine.py`
- **.stop()** (2 connections) — `core/gherkai_core/adapters/fargate_engine.py`
- **.__init__()** (1 connections) — `core/gherkai_core/adapters/fargate_engine.py`
- **一个正在运行的 Fargate task 的句柄。stop() 翻成 StopTask（ADR 0026 机制层，对称…** (1 connections) — `core/gherkai_core/adapters/fargate_engine.py`
- **请求优雅停止即调 StopTask。 **grace_period_s 在 Fargate 上无法逐次传**（ADR 0024/0032）：容器…** (1 connections) — `core/gherkai_core/adapters/fargate_engine.py`
- **按序返回 describe_tasks 响应的假 ecs（模拟 STOPPED 翻转后 exitCode 落值时序）。** (1 connections) — `core/tests/test_fargate_engine.py`
- **.describe_tasks()** (1 connections) — `core/tests/test_fargate_engine.py`
- **.__init__()** (1 connections) — `core/tests/test_fargate_engine.py`

## Relationships

- [Run Definition Domain Model](Run_Definition_Domain_Model.md) (4 shared connections)
- [Worker Log Event Formatting](Worker_Log_Event_Formatting.md) (4 shared connections)
- [Fargate Engine Tests](Fargate_Engine_Tests.md) (3 shared connections)
- [Fargate Engine Adapter](Fargate_Engine_Adapter.md) (2 shared connections)
- [Event Gap Grace Tests](Event_Gap_Grace_Tests.md) (2 shared connections)
- [Core Adapters Documentation](Core_Adapters_Documentation.md) (1 shared connections)
- [ECS Task Exit Probing](ECS_Task_Exit_Probing.md) (1 shared connections)
- [Event Records Projection](Event_Records_Projection.md) (1 shared connections)
- [Result Tree Text Rendering](Result_Tree_Text_Rendering.md) (1 shared connections)

## Source Files

- `core/gherkai_core/adapters/fargate_engine.py`
- `core/tests/test_fargate_engine.py`

## Audit Trail

- EXTRACTED: 12 (44%)
- INFERRED: 15 (56%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*