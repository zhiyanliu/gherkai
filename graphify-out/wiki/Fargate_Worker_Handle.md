# Fargate Worker Handle

> 24 nodes · cohesion 0.09

## Key Concepts

- **_MissingThenStoppedEcs** (17 connections) — `core/tests/test_fargate_engine.py`
- **_RoundsTable** (16 connections) — `core/tests/test_fargate_engine.py`
- **_FakeEcs** (15 connections) — `core/tests/test_fargate_engine.py`
- **_SeqEcs** (15 connections) — `core/tests/test_fargate_engine.py`
- **FargateWorkerHandle** (12 connections) — `core/gherkai_core/adapters/fargate_engine.py`
- **test_read_events_transient_missing_then_events_and_stopped()** (6 connections) — `core/tests/test_fargate_engine.py`
- **test_read_events_persistent_missing_task_raises_after_grace()** (5 connections) — `core/tests/test_fargate_engine.py`
- **.stop()** (2 connections) — `core/gherkai_core/adapters/fargate_engine.py`
- **.__init__()** (1 connections) — `core/gherkai_core/adapters/fargate_engine.py`
- **一个在跑的 Fargate task 的句柄。stop() 翻成 StopTask（ADR 0026 机制层，对称…** (1 connections) — `core/gherkai_core/adapters/fargate_engine.py`
- **请求优雅停止 = StopTask。 **grace_period_s 在 Fargate 上无法逐次传**（ADR 0024/0032）：容器…** (1 connections) — `core/gherkai_core/adapters/fargate_engine.py`
- **.describe_tasks()** (1 connections) — `core/tests/test_fargate_engine.py`
- **.__init__()** (1 connections) — `core/tests/test_fargate_engine.py`
- **.describe_tasks()** (1 connections) — `core/tests/test_fargate_engine.py`
- **.__init__()** (1 connections) — `core/tests/test_fargate_engine.py`
- **构造 describe_tasks 响应的假 ecs client（moto exitCode 恒 0、lastStatus 由 describe…** (1 connections) — `core/tests/test_fargate_engine.py`
- **按序返回 describe_tasks 响应的假 ecs（模拟 STOPPED 翻转后 exitCode 落值时序）。** (1 connections) — `core/tests/test_fargate_engine.py`
- **前 missing_calls 次 describe → MISSING，之后 STOPPED exit 0。** (1 connections) — `core/tests/test_fargate_engine.py`
- **无事件 + DescribeTasks 恒 MISSING → 连续超过宽限即抛可归因 RuntimeError（曾把空 tasks 当「未…** (1 connections) — `core/tests/test_fargate_engine.py`
- **瞬时 MISSING（ECS 最终一致）→ 宽限内恢复 → 事件照常读、scope_done 后读到 exit 0，不误报。** (1 connections) — `core/tests/test_fargate_engine.py`
- **.__init__()** (1 connections) — `core/tests/test_fargate_engine.py`
- **.query()** (1 connections) — `core/tests/test_fargate_engine.py`
- **.describe_tasks()** (1 connections) — `core/tests/test_fargate_engine.py`
- **.__init__()** (1 connections) — `core/tests/test_fargate_engine.py`

## Relationships

- [Job Explain & S3 Offload](Job_Explain_%26_S3_Offload.md) (13 shared connections)
- [Fargate Engine Tests](Fargate_Engine_Tests.md) (9 shared connections)
- [Event Formatting](Event_Formatting.md) (9 shared connections)
- [Fargate Engine](Fargate_Engine.md) (5 shared connections)
- [Cloud Boto3 Guards & EventLog](Cloud_Boto3_Guards_%26_EventLog.md) (5 shared connections)
- [Event Gap Reading Tests](Event_Gap_Reading_Tests.md) (5 shared connections)
- [Typed Errors & Severity](Typed_Errors_%26_Severity.md) (4 shared connections)
- [Run State Projection](Run_State_Projection.md) (4 shared connections)

## Source Files

- `core/gherkai_core/adapters/fargate_engine.py`
- `core/tests/test_fargate_engine.py`

## Audit Trail

- EXTRACTED: 37 (47%)
- INFERRED: 42 (53%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*