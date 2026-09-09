# Scope Done vs ECS Stopped

> 4 nodes · cohesion 0.50

## Key Concepts

- **test_read_events_scope_done_waits_for_stopped_before_reading_exit()** (6 connections) — `core/tests/test_fargate_engine.py`
- **_delayed_stopped_ecs()** (3 connections) — `core/tests/test_fargate_engine.py`
- ****option-c 定义行为的核心守卫**：scope_done 先于 ECS STOPPED ~11s 到达（ADR 0032 结论…** (1 connections) — `core/tests/test_fargate_engine.py`
- **假 ecs：前 running_polls 次 describe_tasks 返回 RUNNING（exitCode 尚 null），之后才 STOPPED。…** (1 connections) — `core/tests/test_fargate_engine.py`

## Relationships

- [Fargate Event Drain & Exit Codes](Fargate_Event_Drain_%26_Exit_Codes.md) (3 shared connections)
- [Fargate Engine Unit Tests](Fargate_Engine_Unit_Tests.md) (2 shared connections)

## Source Files

- `core/tests/test_fargate_engine.py`

## Audit Trail

- EXTRACTED: 8 (100%)
- INFERRED: 0 (0%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*