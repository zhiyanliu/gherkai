# Subprocess Worker Launcher

> 7 nodes · cohesion 0.29

## Key Concepts

- **SubprocessLauncher** (15 connections) — `runtime/gherkai_runtime/detached.py`
- **.__init__()** (3 connections) — `runtime/gherkai_runtime/detached.py`
- **.launch()** (2 connections) — `runtime/gherkai_runtime/detached.py`
- **._pump()** (2 connections) — `runtime/gherkai_runtime/detached.py`
- **Job** (1 connections)
- **local Launcher（ADR 0034 机制四回调 + 机制二退出观察者）。 launch(job)：起 worker（resolver 按…** (1 connections) — `runtime/gherkai_runtime/detached.py`
- **驱动一个 worker 的 fd3 事件流跑完（落库在 raw_sink 里做）；结束后 handle.wait() 拿 exitcode 写…** (1 connections) — `runtime/gherkai_runtime/detached.py`

## Relationships

- [Detached Launcher Reconcile](Detached_Launcher_Reconcile.md) (2 shared connections)
- [Reconcile Loop Integration](Reconcile_Loop_Integration.md) (2 shared connections)
- [S3 ReportStore & Subprocess Engine](S3_ReportStore_%26_Subprocess_Engine.md) (2 shared connections)
- [Timestamp and Clock Utilities](Timestamp_and_Clock_Utilities.md) (1 shared connections)
- [Local Detached Run Wiring](Local_Detached_Run_Wiring.md) (1 shared connections)
- [Engine Ports & Adapters](Engine_Ports_%26_Adapters.md) (1 shared connections)
- [Run State Rendering & Boto Guard](Run_State_Rendering_%26_Boto_Guard.md) (1 shared connections)
- [Run Result Verdict Model](Run_Result_Verdict_Model.md) (1 shared connections)
- [Render & ReportStore Local](Render_%26_ReportStore_Local.md) (1 shared connections)
- [SQLite Event Log Store](SQLite_Event_Log_Store.md) (1 shared connections)

## Source Files

- `runtime/gherkai_runtime/detached.py`

## Audit Trail

- EXTRACTED: 14 (74%)
- INFERRED: 5 (26%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*