# Event Gap Grace Tests

> 18 nodes · cohesion 0.14

## Key Concepts

- **_MissingThenStoppedEcs** (17 connections) — `core/tests/test_fargate_engine.py`
- **_RoundsTable** (16 connections) — `core/tests/test_fargate_engine.py`
- **_gap_engine()** (8 connections) — `core/tests/test_fargate_engine.py`
- **test_read_events_progress_resets_missing_count()** (6 connections) — `core/tests/test_fargate_engine.py`
- **test_read_events_transient_missing_then_events_and_stopped()** (6 connections) — `core/tests/test_fargate_engine.py`
- **test_read_events_persistent_missing_task_raises_after_grace()** (5 connections) — `core/tests/test_fargate_engine.py`
- **test_read_events_gap_beyond_grace_is_skipped_with_warning()** (4 connections) — `core/tests/test_fargate_engine.py`
- **_ev_item()** (3 connections) — `core/tests/test_fargate_engine.py`
- **.describe_tasks()** (1 connections) — `core/tests/test_fargate_engine.py`
- **.__init__()** (1 connections) — `core/tests/test_fargate_engine.py`
- **裸构造：只装 _read_events 路径要用的属性（不起 RunTask）。** (1 connections) — `core/tests/test_fargate_engine.py`
- **洞在宽限后仍在，就是写者侧真丢（PutItem 失败、seq 已耗）→ 记警告、越过继续，流式读不无界停摆。** (1 connections) — `core/tests/test_fargate_engine.py`
- **前 missing_calls 次 describe → MISSING，之后 STOPPED exit 0。** (1 connections) — `core/tests/test_fargate_engine.py`
- **无事件 + DescribeTasks 恒 MISSING → 连续超过宽限即抛可归因 RuntimeError（曾把空 tasks 当「未…** (1 connections) — `core/tests/test_fargate_engine.py`
- **瞬时 MISSING（ECS 最终一致）→ 宽限内恢复 → 事件照常读、scope_done 后读到 exit 0，不误报。** (1 connections) — `core/tests/test_fargate_engine.py`
- **「连续 MISSING」的连续性被有进展的轮次打断：事件/空轮交替、空轮都探到 MISSING，累计 3 次但从不连续 2 次， 宽限 1…** (1 connections) — `core/tests/test_fargate_engine.py`
- **.__init__()** (1 connections) — `core/tests/test_fargate_engine.py`
- **.query()** (1 connections) — `core/tests/test_fargate_engine.py`

## Relationships

- [Fargate Engine Tests](Fargate_Engine_Tests.md) (8 shared connections)
- [Worker Log Event Formatting](Worker_Log_Event_Formatting.md) (6 shared connections)
- [Run Definition Domain Model](Run_Definition_Domain_Model.md) (6 shared connections)
- [Fargate Engine Adapter](Fargate_Engine_Adapter.md) (3 shared connections)
- [Fargate Worker Handle](Fargate_Worker_Handle.md) (2 shared connections)
- [Event Records Projection](Event_Records_Projection.md) (2 shared connections)
- [Result Tree Text Rendering](Result_Tree_Text_Rendering.md) (2 shared connections)
- [Event Sequence Gap Handling](Event_Sequence_Gap_Handling.md) (1 shared connections)
- [Worker Exit Drain Tests](Worker_Exit_Drain_Tests.md) (1 shared connections)

## Source Files

- `core/tests/test_fargate_engine.py`

## Audit Trail

- EXTRACTED: 33 (62%)
- INFERRED: 20 (38%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*