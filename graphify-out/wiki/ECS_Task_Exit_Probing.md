# ECS Task Exit Probing

> 12 nodes · cohesion 0.17

## Key Concepts

- **_FakeEcs** (15 connections) — `core/tests/test_fargate_engine.py`
- **_engine_with_fake_ecs()** (8 connections) — `core/tests/test_fargate_engine.py`
- **test_await_exit_code_missing_task_beyond_grace_raises()** (3 connections) — `core/tests/test_fargate_engine.py`
- **test_probe_task_missing_is_a_third_state_not_running()** (3 connections) — `core/tests/test_fargate_engine.py`
- **test_probe_task_not_stopped()** (2 connections) — `core/tests/test_fargate_engine.py`
- **test_probe_task_stopped_but_exit_code_null()** (2 connections) — `core/tests/test_fargate_engine.py`
- **test_probe_task_stopped_with_exit_code()** (2 connections) — `core/tests/test_fargate_engine.py`
- **.describe_tasks()** (1 connections) — `core/tests/test_fargate_engine.py`
- **.__init__()** (1 connections) — `core/tests/test_fargate_engine.py`
- **构造 describe_tasks 响应的假 ecs client（moto exitCode 恒 0、lastStatus 由 describe…** (1 connections) — `core/tests/test_fargate_engine.py`
- **DescribeTasks 空 tasks + failures MISSING → missing=True（不是「未 STOPPED」）：ECS…** (1 connections) — `core/tests/test_fargate_engine.py`
- **持续 MISSING 超过有界宽限 → 抛可归因 RuntimeError（schedule 记 error），不再无上界轮询。** (1 connections) — `core/tests/test_fargate_engine.py`

## Relationships

- [Fargate Engine Tests](Fargate_Engine_Tests.md) (7 shared connections)
- [Worker Log Event Formatting](Worker_Log_Event_Formatting.md) (3 shared connections)
- [Run Definition Domain Model](Run_Definition_Domain_Model.md) (3 shared connections)
- [Fargate Engine Adapter](Fargate_Engine_Adapter.md) (2 shared connections)
- [Fargate Worker Handle](Fargate_Worker_Handle.md) (1 shared connections)
- [Event Records Projection](Event_Records_Projection.md) (1 shared connections)
- [Result Tree Text Rendering](Result_Tree_Text_Rendering.md) (1 shared connections)

## Source Files

- `core/tests/test_fargate_engine.py`

## Audit Trail

- EXTRACTED: 19 (66%)
- INFERRED: 10 (34%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*