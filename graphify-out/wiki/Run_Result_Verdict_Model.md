# Run Result Verdict Model

> 89 nodes · cohesion 0.05

## Key Concepts

- **Status** (93 connections) — `core/gherkai_core/model.py`
- **JobResult** (72 connections) — `core/gherkai_core/model.py`
- **RunResult** (56 connections) — `core/gherkai_core/model.py`
- **schedule.py** (30 connections) — `core/gherkai_core/schedule.py`
- **ports.py** (26 connections) — `core/gherkai_core/ports.py`
- **ResultStore** (24 connections) — `core/gherkai_core/ports.py`
- **Engine** (22 connections) — `core/gherkai_core/ports.py`
- **ReportStore** (22 connections) — `core/gherkai_core/ports.py`
- **reconcile.py** (21 connections) — `core/gherkai_core/reconcile.py`
- **_Worker** (21 connections) — `core/gherkai_core/schedule.py`
- **persist.py** (18 connections) — `core/gherkai_core/persist.py`
- **EngineResolver** (16 connections) — `core/gherkai_core/ports.py`
- **Sink** (16 connections) — `core/gherkai_core/ports.py`
- **JobSink** (15 connections) — `core/gherkai_core/ports.py`
- **test_s3_result_store.py** (15 connections) — `core/tests/test_s3_result_store.py`
- **_Heartbeat** (14 connections) — `core/gherkai_core/schedule.py`
- **_job_def()** (14 connections) — `core/tests/test_stores.py`
- **WorkerHandle** (12 connections) — `core/gherkai_core/ports.py`
- **reduce_event()** (11 connections) — `core/gherkai_core/project.py`
- **._run_once()** (9 connections) — `core/gherkai_core/schedule.py`
- **test_render_text_annotates_shortcircuited_step()** (8 connections) — `cli/tests/test_render.py`
- **test_render_text_no_annotation_on_plain_failed()** (8 connections) — `cli/tests/test_render.py`
- **Protocol** (8 connections)
- **.__init__()** (7 connections) — `core/gherkai_core/schedule.py`
- **._reduce()** (6 connections) — `core/gherkai_core/schedule.py`
- *... and 64 more nodes in this community*

## Relationships

- [Engine Ports & Adapters](Engine_Ports_%26_Adapters.md) (42 shared connections)
- [Run State Rendering & Boto Guard](Run_State_Rendering_%26_Boto_Guard.md) (41 shared connections)
- [SQLite Event Log & Projection](SQLite_Event_Log_%26_Projection.md) (34 shared connections)
- [DynamoDB RunStore Conditional Writes](DynamoDB_RunStore_Conditional_Writes.md) (33 shared connections)
- [Render & ReportStore Local](Render_%26_ReportStore_Local.md) (28 shared connections)
- [Run Persistence Orchestration](Run_Persistence_Orchestration.md) (19 shared connections)
- [Run Schedule Orchestration](Run_Schedule_Orchestration.md) (16 shared connections)
- [S3 ReportStore & Subprocess Engine](S3_ReportStore_%26_Subprocess_Engine.md) (16 shared connections)
- [ResultStore Local/S3](ResultStore_Local-S3.md) (14 shared connections)
- [Terminal Status Aggregation](Terminal_Status_Aggregation.md) (14 shared connections)
- [Reconcile Ports & Tick](Reconcile_Ports_%26_Tick.md) (7 shared connections)
- [Event Formatting & Cost Model](Event_Formatting_%26_Cost_Model.md) (7 shared connections)

## Source Files

- `CONTEXT.md`
- `cli/tests/test_render.py`
- `core/README.md`
- `core/gherkai_core/adapters/run_store/ddb.py`
- `core/gherkai_core/model.py`
- `core/gherkai_core/persist.py`
- `core/gherkai_core/ports.py`
- `core/gherkai_core/project.py`
- `core/gherkai_core/reconcile.py`
- `core/gherkai_core/schedule.py`
- `core/tests/test_s3_result_store.py`
- `core/tests/test_stores.py`

## Audit Trail

- EXTRACTED: 351 (69%)
- INFERRED: 156 (31%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*