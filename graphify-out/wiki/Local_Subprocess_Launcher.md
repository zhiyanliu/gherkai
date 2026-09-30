# Local Subprocess Launcher

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

- [Local Reconcile Loop Tests](Local_Reconcile_Loop_Tests.md) (4 shared connections)
- [Run Result Aggregation Tree](Run_Result_Aggregation_Tree.md) (3 shared connections)
- [Local Detached Execution](Local_Detached_Execution.md) (2 shared connections)
- [Wall Clock Timestamps](Wall_Clock_Timestamps.md) (2 shared connections)
- [Job Domain Models](Job_Domain_Models.md) (2 shared connections)
- [Local Report Store](Local_Report_Store.md) (1 shared connections)
- [SQLite Event Log](SQLite_Event_Log.md) (1 shared connections)

## Source Files

- `runtime/gherkai_runtime/detached.py`

## Audit Trail

- EXTRACTED: 18 (78%)
- INFERRED: 5 (22%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*