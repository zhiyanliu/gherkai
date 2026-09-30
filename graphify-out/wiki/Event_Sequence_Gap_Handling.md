# Event Sequence Gap Handling

> 4 nodes · cohesion 0.50

## Key Concepts

- **_delayed_stopped_ecs()** (4 connections) — `core/tests/test_fargate_engine.py`
- **test_read_events_gap_within_grace_waits_and_fills_in_order()** (4 connections) — `core/tests/test_fargate_engine.py`
- **最终一致读先看到 seq 3 却没 seq 2：游标停在 1、下轮 re-query 补到 2 后再往下——事件按 seq 顺序、一条不丢…** (1 connections) — `core/tests/test_fargate_engine.py`
- **假 ecs：前 running_polls 次 describe_tasks 返回 RUNNING（exitCode 尚 null），之后才 STOPPED。…** (1 connections) — `core/tests/test_fargate_engine.py`

## Relationships

- [Fargate Engine Tests](Fargate_Engine_Tests.md) (2 shared connections)
- [Cloud Event Drain Tests](Cloud_Event_Drain_Tests.md) (1 shared connections)
- [Event Gap & ECS Polling](Event_Gap_%26_ECS_Polling.md) (1 shared connections)

## Source Files

- `core/tests/test_fargate_engine.py`

## Audit Trail

- EXTRACTED: 7 (100%)
- INFERRED: 0 (0%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*