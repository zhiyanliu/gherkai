# Event Gap Reading Tests

> 11 nodes · cohesion 0.18

## Key Concepts

- **_gap_engine()** (8 connections) — `core/tests/test_fargate_engine.py`
- **test_read_events_progress_resets_missing_count()** (6 connections) — `core/tests/test_fargate_engine.py`
- **_delayed_stopped_ecs()** (4 connections) — `core/tests/test_fargate_engine.py`
- **test_read_events_gap_beyond_grace_is_skipped_with_warning()** (4 connections) — `core/tests/test_fargate_engine.py`
- **test_read_events_gap_within_grace_waits_and_fills_in_order()** (4 connections) — `core/tests/test_fargate_engine.py`
- **_ev_item()** (3 connections) — `core/tests/test_fargate_engine.py`
- **裸构造：只装 _read_events 路径要用的属性（不起 RunTask）。** (1 connections) — `core/tests/test_fargate_engine.py`
- **最终一致读先看到 seq 3 却没 seq 2：游标停在 1、下轮 re-query 补到 2 后再往下——事件按 seq 顺序、一条不丢…** (1 connections) — `core/tests/test_fargate_engine.py`
- **洞在宽限后仍在 = 写者侧真丢（PutItem 失败、seq 已耗）→ 记警告、越过继续，流式读不无界停摆。** (1 connections) — `core/tests/test_fargate_engine.py`
- **假 ecs：前 running_polls 次 describe_tasks 返回 RUNNING（exitCode 尚 null），之后才 STOPPED。…** (1 connections) — `core/tests/test_fargate_engine.py`
- **「连续 MISSING」的连续性被有进展的轮次打断：事件/空轮交替、空轮都探到 MISSING，累计 3 次但从不连续 2 次， 宽限 1…** (1 connections) — `core/tests/test_fargate_engine.py`

## Relationships

- [Fargate Engine Tests](Fargate_Engine_Tests.md) (6 shared connections)
- [Fargate Worker Handle](Fargate_Worker_Handle.md) (5 shared connections)
- [Fargate Exit Code Tests](Fargate_Exit_Code_Tests.md) (2 shared connections)
- [Fargate Engine](Fargate_Engine.md) (1 shared connections)

## Source Files

- `core/tests/test_fargate_engine.py`

## Audit Trail

- EXTRACTED: 24 (100%)
- INFERRED: 0 (0%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*