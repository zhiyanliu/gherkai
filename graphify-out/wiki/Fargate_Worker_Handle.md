# Fargate Worker Handle

> 13 nodes · cohesion 0.15

## Key Concepts

- **_FakeEcs** (15 connections) — `core/tests/test_fargate_engine.py`
- **FargateWorkerHandle** (10 connections) — `core/gherkai_core/adapters/fargate_engine.py`
- **_engine_with_fake_ecs()** (6 connections) — `core/tests/test_fargate_engine.py`
- **.stop()** (2 connections) — `core/gherkai_core/adapters/fargate_engine.py`
- **test_probe_task_not_stopped()** (2 connections) — `core/tests/test_fargate_engine.py`
- **test_probe_task_stopped_but_exit_code_null()** (2 connections) — `core/tests/test_fargate_engine.py`
- **test_probe_task_stopped_with_exit_code()** (2 connections) — `core/tests/test_fargate_engine.py`
- **.__init__()** (1 connections) — `core/gherkai_core/adapters/fargate_engine.py`
- **一个在跑的 Fargate task 的句柄。stop() 翻成 StopTask（ADR 0026 机制层，对称…** (1 connections) — `core/gherkai_core/adapters/fargate_engine.py`
- **请求优雅停止 = StopTask。 **grace_period_s 在 Fargate 上无法逐次传**（ADR 0024/0032）：容器…** (1 connections) — `core/gherkai_core/adapters/fargate_engine.py`
- **.describe_tasks()** (1 connections) — `core/tests/test_fargate_engine.py`
- **.__init__()** (1 connections) — `core/tests/test_fargate_engine.py`
- **构造 describe_tasks 响应的假 ecs client（moto exitCode 恒 0、lastStatus 由 describe…** (1 connections) — `core/tests/test_fargate_engine.py`

## Relationships

- [Fargate Engine Tests](Fargate_Engine_Tests.md) (6 shared connections)
- [Engine Ports & Adapters](Engine_Ports_%26_Adapters.md) (5 shared connections)
- [Fargate Engine](Fargate_Engine.md) (3 shared connections)
- [Event Progress Formatting](Event_Progress_Formatting.md) (3 shared connections)
- [Exit Code Await Polling](Exit_Code_Await_Polling.md) (1 shared connections)
- [Terminal Status Aggregation](Terminal_Status_Aggregation.md) (1 shared connections)
- [State Projection & Planning](State_Projection_%26_Planning.md) (1 shared connections)
- [Boto Guard & S3 Offload](Boto_Guard_%26_S3_Offload.md) (1 shared connections)

## Source Files

- `core/gherkai_core/adapters/fargate_engine.py`
- `core/tests/test_fargate_engine.py`

## Audit Trail

- EXTRACTED: 20 (61%)
- INFERRED: 13 (39%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*