# Event Record Reading

> 4 nodes · cohesion 0.50

## Key Concepts

- **.records()** (7 connections) — `core/gherkai_core/adapters/event_log/ddb.py`
- **._emit_ts()** (3 connections) — `core/gherkai_core/adapters/event_log/ddb.py`
- **读某 run 全量 records（逐 scope Query worker 段 events + 取 task_exited）→ 供 project…** (1 connections) — `core/gherkai_core/adapters/event_log/ddb.py`
- **从 events item 还原 worker emit 墙钟（reduce_event 的 now，供算时长）。 写端（worker EventSink）写…** (1 connections) — `core/gherkai_core/adapters/event_log/ddb.py`

## Relationships

- [Cloud Job Launcher](Cloud_Job_Launcher.md) (3 shared connections)
- [Event Formatting](Event_Formatting.md) (1 shared connections)
- [Cloud Boto3 Guards & EventLog](Cloud_Boto3_Guards_%26_EventLog.md) (1 shared connections)
- [Run State Projection](Run_State_Projection.md) (1 shared connections)

## Source Files

- `core/gherkai_core/adapters/event_log/ddb.py`

## Audit Trail

- EXTRACTED: 9 (100%)
- INFERRED: 0 (0%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*