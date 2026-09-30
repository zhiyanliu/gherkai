# Worker Emit Timestamp

> 2 nodes · cohesion 1.00

## Key Concepts

- **._emit_ts()** (3 connections) — `core/gherkai_core/adapters/event_log/ddb.py`
- **从 events item 还原 worker emit 墙钟（reduce_event 的 now，供算时长）。 写端（worker EventSink）写…** (1 connections) — `core/gherkai_core/adapters/event_log/ddb.py`

## Relationships

- [Event Records Projection](Event_Records_Projection.md) (1 shared connections)
- [Cloud Launcher and EventLog](Cloud_Launcher_and_EventLog.md) (1 shared connections)

## Source Files

- `core/gherkai_core/adapters/event_log/ddb.py`

## Audit Trail

- EXTRACTED: 3 (100%)
- INFERRED: 0 (0%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*