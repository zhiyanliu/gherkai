# Event Log Adapters

> 43 nodes · cohesion 0.08

## Key Concepts

- **ScopeDone** (40 connections) — `core/gherkai_core/model.py`
- **project.py** (39 connections) — `core/gherkai_core/project.py`
- **EventRecord** (36 connections) — `core/gherkai_core/project.py`
- **TaskExited** (29 connections) — `core/gherkai_core/project.py`
- **schedule.py** (28 connections) — `core/gherkai_core/schedule.py`
- **Timing** (24 connections) — `core/gherkai_core/project.py`
- **Action** (21 connections) — `core/gherkai_core/project.py`
- **NonTerminalSnapshot** (21 connections) — `core/gherkai_core/project.py`
- **StepSkipped** (16 connections) — `core/gherkai_core/model.py`
- **StepStarted** (15 connections) — `core/gherkai_core/model.py`
- **event_log/ddb.py** (12 connections) — `core/gherkai_core/adapters/event_log/ddb.py`
- **event_log/__init__.py** (11 connections) — `core/gherkai_core/adapters/event_log/__init__.py`
- **reduce_event()** (11 connections) — `core/gherkai_core/project.py`
- **_reduce_scope()** (11 connections) — `core/gherkai_core/project.py`
- **sqlite.py** (8 connections) — `core/gherkai_core/adapters/event_log/sqlite.py`
- **_lifecycle_rank()** (7 connections) — `core/gherkai_core/project.py`
- **test_projection_lands_running_once_any_job_advanced()** (7 connections) — `core/tests/test_conditional_writes.py`
- **test_projection_preserves_claimed_at()** (7 connections) — `core/tests/test_conditional_writes.py`
- **test_projection_without_baseline_keeps_stored_lineage()** (7 connections) — `core/tests/test_conditional_writes.py`
- **_job_status()** (6 connections) — `core/gherkai_core/project.py`
- **.project_state()** (5 connections) — `core/gherkai_core/adapters/run_store/ddb.py`
- **DdbEventLog（ADR 0034 cloud 侧）：cloud 无状态批量运行的 EventLog——从 DDB events 表读全量重放 + 写…** (1 connections) — `core/gherkai_core/adapters/event_log/ddb.py`
- **events 日志 adapter（ADR 0034）：持久事件通道，reconciler 从此全量重放推演 RunState。…** (1 connections) — `core/gherkai_core/adapters/event_log/__init__.py`
- **SqliteEventLog（ADR 0034）：local 无状态批量运行的持久事件通道。 worker 事件（原始 ADR 0024 JSON 行 +…** (1 connections) — `core/gherkai_core/adapters/event_log/sqlite.py`
- **HWM 条件写 STATE：仅当 (传入 hwm ≥ 库中 hwm) 且 (库中未 finalize) 才写（机制三①）。CCF → stale/已终态 →…** (1 connections) — `core/gherkai_core/adapters/run_store/ddb.py`
- *... and 18 more nodes in this community*

## Relationships

- [Run State Projection](Run_State_Projection.md) (42 shared connections)
- [Run Result Aggregation Tree](Run_Result_Aggregation_Tree.md) (34 shared connections)
- [Event Formatting](Event_Formatting.md) (26 shared connections)
- [Job Domain Models](Job_Domain_Models.md) (21 shared connections)
- [Run Scheduling Core](Run_Scheduling_Core.md) (20 shared connections)
- [Run State Store](Run_State_Store.md) (18 shared connections)
- [Typed Errors and Wire Protocol](Typed_Errors_and_Wire_Protocol.md) (14 shared connections)
- [Result Store & Report Refs](Result_Store_%26_Report_Refs.md) (14 shared connections)
- [SQLite Event Log](SQLite_Event_Log.md) (8 shared connections)
- [Cloud Store Adapters](Cloud_Store_Adapters.md) (8 shared connections)
- [Cloud Reconcile Tests](Cloud_Reconcile_Tests.md) (6 shared connections)
- [Job Worker Execution](Job_Worker_Execution.md) (5 shared connections)

## Source Files

- `core/gherkai_core/adapters/event_log/__init__.py`
- `core/gherkai_core/adapters/event_log/ddb.py`
- `core/gherkai_core/adapters/event_log/sqlite.py`
- `core/gherkai_core/adapters/run_store/ddb.py`
- `core/gherkai_core/model.py`
- `core/gherkai_core/project.py`
- `core/gherkai_core/schedule.py`
- `core/tests/test_conditional_writes.py`

## Audit Trail

- EXTRACTED: 212 (68%)
- INFERRED: 100 (32%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*