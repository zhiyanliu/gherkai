# Fargate Worker Handle

> 14 nodes · cohesion 0.16

## Key Concepts

- **_SeqEcs** (15 connections) — `core/tests/test_fargate_engine.py`
- **FargateWorkerHandle** (12 connections) — `core/gherkai_core/adapters/fargate_engine.py`
- **_await_engine()** (6 connections) — `core/tests/test_fargate_engine.py`
- **_stopped_resp()** (4 connections) — `core/tests/test_fargate_engine.py`
- **test_await_exit_code_null_beyond_grace_settles_as_error()** (3 connections) — `core/tests/test_fargate_engine.py`
- **test_await_exit_code_null_then_nonzero_landed_preserved()** (3 connections) — `core/tests/test_fargate_engine.py`
- **test_await_exit_code_waits_out_null_then_reads_landed_code()** (3 connections) — `core/tests/test_fargate_engine.py`
- **.stop()** (2 connections) — `core/gherkai_core/adapters/fargate_engine.py`
- **.__init__()** (1 connections) — `core/gherkai_core/adapters/fargate_engine.py`
- **一个正在运行的 Fargate task 的句柄。stop() 翻成 StopTask（ADR 0026 机制层，对称…** (1 connections) — `core/gherkai_core/adapters/fargate_engine.py`
- **请求优雅停止即调 StopTask。 **grace_period_s 在 Fargate 上无法逐次传**（ADR 0024/0032）：容器…** (1 connections) — `core/gherkai_core/adapters/fargate_engine.py`
- **按序返回 describe_tasks 响应的假 ecs（模拟 STOPPED 翻转后 exitCode 落值时序）。** (1 connections) — `core/tests/test_fargate_engine.py`
- **.describe_tasks()** (1 connections) — `core/tests/test_fargate_engine.py`
- **.__init__()** (1 connections) — `core/tests/test_fargate_engine.py`

## Relationships

- [Fargate Engine Tests](Fargate_Engine_Tests.md) (7 shared connections)
- [Run Metadata & S3 Offload](Run_Metadata_%26_S3_Offload.md) (4 shared connections)
- [Fargate Engine Adapter](Fargate_Engine_Adapter.md) (3 shared connections)
- [Event Progress Formatting](Event_Progress_Formatting.md) (3 shared connections)
- [Fargate Event Read Tests](Fargate_Event_Read_Tests.md) (2 shared connections)
- [DynamoDB Event Log](DynamoDB_Event_Log.md) (1 shared connections)
- [ECS Task Probe Tests](ECS_Task_Probe_Tests.md) (1 shared connections)
- [Core Typed Errors](Core_Typed_Errors.md) (1 shared connections)
- [Event Log & Projection](Event_Log_%26_Projection.md) (1 shared connections)
- [Run State Rendering](Run_State_Rendering.md) (1 shared connections)

## Source Files

- `core/gherkai_core/adapters/fargate_engine.py`
- `core/tests/test_fargate_engine.py`

## Audit Trail

- EXTRACTED: 24 (62%)
- INFERRED: 15 (38%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*