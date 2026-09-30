# Run Result Aggregation Tree

> 108 nodes · cohesion 0.04

## Key Concepts

- **Status** (106 connections) — `core/gherkai_core/model.py`
- **JobResult** (84 connections) — `core/gherkai_core/model.py`
- **RunResult** (65 connections) — `core/gherkai_core/model.py`
- **RunStore** (34 connections) — `core/gherkai_core/ports.py`
- **ResultStore** (28 connections) — `core/gherkai_core/ports.py`
- **ports.py** (27 connections) — `core/gherkai_core/ports.py`
- **Engine** (22 connections) — `core/gherkai_core/ports.py`
- **ReportStore** (22 connections) — `core/gherkai_core/ports.py`
- **SubprocessEngine** (21 connections) — `core/gherkai_core/adapters/subprocess_engine.py`
- **test_render.py** (20 connections) — `cli/tests/test_render.py`
- **persist.py** (17 connections) — `core/gherkai_core/persist.py`
- **EngineResolver** (16 connections) — `core/gherkai_core/ports.py`
- **JobSink** (15 connections) — `core/gherkai_core/ports.py`
- **_UnavailableEngine** (15 connections) — `runtime/gherkai_runtime/compose.py`
- **WorkerNotFoundError** (15 connections) — `runtime/gherkai_runtime/compose.py`
- **WorkerSelfDescribeError** (15 connections) — `runtime/gherkai_runtime/compose.py`
- **Sink** (14 connections) — `core/gherkai_core/ports.py`
- **_Heartbeat** (14 connections) — `core/gherkai_core/schedule.py`
- **CloudTarget** (14 connections) — `runtime/gherkai_runtime/compose.py`
- **WorkerResolution** (14 connections) — `runtime/gherkai_runtime/compose.py`
- **render_text()** (13 connections) — `cli/gherkai_cli/render.py`
- **WorkerCmd** (13 connections) — `runtime/gherkai_runtime/compose.py`
- **WorkerHandle** (12 connections) — `core/gherkai_core/ports.py`
- **_sample_run()** (11 connections) — `cli/tests/test_render.py`
- **test_run_tree_attaches_reason_and_refs_under_their_step()** (10 connections) — `cli/tests/test_render.py`
- *... and 83 more nodes in this community*

## Relationships

- [Job Domain Models](Job_Domain_Models.md) (64 shared connections)
- [Cloud Store Adapters](Cloud_Store_Adapters.md) (36 shared connections)
- [Event Log Adapters](Event_Log_Adapters.md) (34 shared connections)
- [Local Result Store](Local_Result_Store.md) (23 shared connections)
- [Result Store & Report Refs](Result_Store_%26_Report_Refs.md) (21 shared connections)
- [Run State Store](Run_State_Store.md) (20 shared connections)
- [S3 Store Adapters](S3_Store_Adapters.md) (18 shared connections)
- [SSM Path Naming](SSM_Path_Naming.md) (16 shared connections)
- [Local Report Store](Local_Report_Store.md) (14 shared connections)
- [Reconciler Orchestration](Reconciler_Orchestration.md) (13 shared connections)
- [Job Worker Execution](Job_Worker_Execution.md) (11 shared connections)
- [Run Scheduling Core](Run_Scheduling_Core.md) (10 shared connections)

## Source Files

- `cli/gherkai_cli/render.py`
- `cli/tests/test_render.py`
- `core/DEVELOPMENT.md`
- `core/README.md`
- `core/gherkai_core/adapters/subprocess_engine.py`
- `core/gherkai_core/model.py`
- `core/gherkai_core/persist.py`
- `core/gherkai_core/ports.py`
- `core/gherkai_core/schedule.py`
- `runtime/gherkai_runtime/compose.py`

## Audit Trail

- EXTRACTED: 397 (64%)
- INFERRED: 222 (36%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*