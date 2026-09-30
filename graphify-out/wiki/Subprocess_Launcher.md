# Subprocess Launcher

> 9 nodes · cohesion 0.22

## Key Concepts

- **SubprocessLauncher** (17 connections) — `runtime/gherkai_runtime/detached.py`
- **._pump()** (4 connections) — `runtime/gherkai_runtime/detached.py`
- **.__init__()** (3 connections) — `runtime/gherkai_runtime/detached.py`
- **.launch()** (2 connections) — `runtime/gherkai_runtime/detached.py`
- **Event** (1 connections)
- **Job** (1 connections)
- **驱动一个 worker 的 fd3 事件流直到结束（落库在 raw_sink 里做）；结束后 handle.wait() 拿 exitcode 写…** (1 connections) — `runtime/gherkai_runtime/detached.py`
- **local Launcher（ADR 0034 机制四回调 + 机制二退出观察者）。 launch(job)：起 worker（resolver 按…** (1 connections) — `runtime/gherkai_runtime/detached.py`
- **Timer** (1 connections)

## Relationships

- [Detached Reconcile Loop Tests](Detached_Reconcile_Loop_Tests.md) (4 shared connections)
- [Wallclock Timestamp Source](Wallclock_Timestamp_Source.md) (2 shared connections)
- [Worker Log Event Formatting](Worker_Log_Event_Formatting.md) (2 shared connections)
- [Run Definition Domain Model](Run_Definition_Domain_Model.md) (2 shared connections)
- [Local Reconcile Rebuild](Local_Reconcile_Rebuild.md) (1 shared connections)
- [Local Detached Reconcile](Local_Detached_Reconcile.md) (1 shared connections)
- [Result Tree Text Rendering](Result_Tree_Text_Rendering.md) (1 shared connections)
- [Report Store Adapters](Report_Store_Adapters.md) (1 shared connections)
- [SQLite Event Log](SQLite_Event_Log.md) (1 shared connections)

## Source Files

- `runtime/gherkai_runtime/detached.py`

## Audit Trail

- EXTRACTED: 18 (78%)
- INFERRED: 5 (22%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*