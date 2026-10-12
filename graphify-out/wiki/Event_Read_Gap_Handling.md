# Event Read Gap Handling

> 18 nodes · cohesion 0.13

## Key Concepts

- **_RoundsTable** (16 connections) — `core/tests/test_fargate_engine.py`
- **_gap_engine()** (8 connections) — `core/tests/test_fargate_engine.py`
- **test_read_events_progress_resets_missing_count()** (6 connections) — `core/tests/test_fargate_engine.py`
- **test_read_events_transient_missing_then_events_and_stopped()** (6 connections) — `core/tests/test_fargate_engine.py`
- **test_read_events_persistent_missing_task_raises_after_grace()** (5 connections) — `core/tests/test_fargate_engine.py`
- **_delayed_stopped_ecs()** (4 connections) — `core/tests/test_fargate_engine.py`
- **test_read_events_gap_beyond_grace_is_skipped_with_warning()** (4 connections) — `core/tests/test_fargate_engine.py`
- **test_read_events_gap_within_grace_waits_and_fills_in_order()** (4 connections) — `core/tests/test_fargate_engine.py`
- **_ev_item()** (3 connections) — `core/tests/test_fargate_engine.py`
- **裸构造：只装 _read_events 路径要用的属性（不起 RunTask）。** (1 connections) — `core/tests/test_fargate_engine.py`
- **最终一致读先看到 seq 3 却没 seq 2：游标停在 1、下轮 re-query 补到 2 后再往下——事件按 seq 顺序、一条不丢…** (1 connections) — `core/tests/test_fargate_engine.py`
- **洞在宽限后仍在，就是写者侧真丢（PutItem 失败、seq 已耗）→ 记警告、越过继续，流式读不无界停摆。** (1 connections) — `core/tests/test_fargate_engine.py`
- **假 ecs：前 running_polls 次 describe_tasks 返回 RUNNING（exitCode 尚 null），之后才 STOPPED。…** (1 connections) — `core/tests/test_fargate_engine.py`
- **无事件 + DescribeTasks 恒 MISSING → 连续超过宽限即抛可归因 RuntimeError（曾把空 tasks 当「未…** (1 connections) — `core/tests/test_fargate_engine.py`
- **瞬时 MISSING（ECS 最终一致）→ 宽限内恢复 → 事件照常读、scope_done 后读到 exit 0，不误报。** (1 connections) — `core/tests/test_fargate_engine.py`
- **「连续 MISSING」的连续性被有进展的轮次打断：事件/空轮交替、空轮都探到 MISSING，累计 3 次但从不连续 2 次， 宽限 1…** (1 connections) — `core/tests/test_fargate_engine.py`
- **.__init__()** (1 connections) — `core/tests/test_fargate_engine.py`
- **.query()** (1 connections) — `core/tests/test_fargate_engine.py`

## Relationships

- [Fargate Engine Adapter Tests](Fargate_Engine_Adapter_Tests.md) (9 shared connections)
- [Job/Scenario Explain Model](Job-Scenario_Explain_Model.md) (8 shared connections)
- [Cloud Launcher & Fargate Adapters](Cloud_Launcher_%26_Fargate_Adapters.md) (3 shared connections)
- [Fargate Event Drain Tests](Fargate_Event_Drain_Tests.md) (2 shared connections)
- [Event Progress Formatting](Event_Progress_Formatting.md) (2 shared connections)
- [Fake DDB Table & SQLite Records](Fake_DDB_Table_%26_SQLite_Records.md) (1 shared connections)

## Source Files

- `core/tests/test_fargate_engine.py`

## Audit Trail

- EXTRACTED: 35 (78%)
- INFERRED: 10 (22%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*