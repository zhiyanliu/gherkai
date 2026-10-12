# Event Stream Pump

> 4 nodes · cohesion 0.50

## Key Concepts

- **._pump()** (4 connections) — `runtime/gherkai_runtime/detached.py`
- **Event** (1 connections)
- **驱动一个 worker 的 fd3 事件流直到结束（落库在 raw_sink 里做）；结束后 handle.wait() 拿 exitcode 写…** (1 connections) — `runtime/gherkai_runtime/detached.py`
- **Timer** (1 connections)

## Relationships

- [SQLite Event Log Adapter](SQLite_Event_Log_Adapter.md) (1 shared connections)

## Source Files

- `runtime/gherkai_runtime/detached.py`

## Audit Trail

- EXTRACTED: 4 (100%)
- INFERRED: 0 (0%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*