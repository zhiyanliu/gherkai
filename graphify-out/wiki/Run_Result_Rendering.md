# Run Result Rendering

> 121 nodes · cohesion 0.04

## Key Concepts

- **RunMeta** (107 connections) — `core/gherkai_core/model.py`
- **JobResult** (72 connections) — `core/gherkai_core/model.py`
- **RunResult** (56 connections) — `core/gherkai_core/model.py`
- **project.py** (39 connections) — `core/gherkai_core/project.py`
- **RunStore** (34 connections) — `core/gherkai_core/ports.py`
- **EventRecord** (34 connections) — `core/gherkai_core/project.py`
- **schedule.py** (30 connections) — `core/gherkai_core/schedule.py`
- **TaskExited** (28 connections) — `core/gherkai_core/project.py`
- **ports.py** (26 connections) — `core/gherkai_core/ports.py`
- **ResultStore** (24 connections) — `core/gherkai_core/ports.py`
- **Timing** (24 connections) — `core/gherkai_core/project.py`
- **Engine** (22 connections) — `core/gherkai_core/ports.py`
- **ReportStore** (22 connections) — `core/gherkai_core/ports.py`
- **reconcile.py** (21 connections) — `core/gherkai_core/reconcile.py`
- **_Worker** (21 connections) — `core/gherkai_core/schedule.py`
- **persist.py** (18 connections) — `core/gherkai_core/persist.py`
- **render.py** (16 connections) — `cli/gherkai_cli/render.py`
- **EngineResolver** (16 connections) — `core/gherkai_core/ports.py`
- **Sink** (16 connections) — `core/gherkai_core/ports.py`
- **test_render.py** (15 connections) — `cli/tests/test_render.py`
- **JobSink** (15 connections) — `core/gherkai_core/ports.py`
- **event_from_line()** (15 connections) — `core/gherkai_core/wire.py`
- **project_full()** (14 connections) — `core/gherkai_core/project.py`
- **_Heartbeat** (14 connections) — `core/gherkai_core/schedule.py`
- **event_log/ddb.py** (12 connections) — `core/gherkai_core/adapters/event_log/ddb.py`
- *... and 96 more nodes in this community*

## Relationships

- [Engine Ports & Adapters](Engine_Ports_%26_Adapters.md) (65 shared connections)
- [Run State Rendering](Run_State_Rendering.md) (54 shared connections)
- [Event Progress Formatting](Event_Progress_Formatting.md) (44 shared connections)
- [Boto Guard & S3 Offload](Boto_Guard_%26_S3_Offload.md) (32 shared connections)
- [Report Refs & Results](Report_Refs_%26_Results.md) (28 shared connections)
- [SQLite Event Log](SQLite_Event_Log.md) (23 shared connections)
- [Local Result Store](Local_Result_Store.md) (23 shared connections)
- [S3 Report Store & Subprocess](S3_Report_Store_%26_Subprocess.md) (21 shared connections)
- [S3 Result Store](S3_Result_Store.md) (19 shared connections)
- [Run Scheduling Engine](Run_Scheduling_Engine.md) (19 shared connections)
- [State Projection & Planning](State_Projection_%26_Planning.md) (18 shared connections)
- [Terminal Status Aggregation](Terminal_Status_Aggregation.md) (12 shared connections)

## Source Files

- `CONTEXT.md`
- `cli/gherkai_cli/render.py`
- `cli/tests/test_render.py`
- `core/README.md`
- `core/gherkai_core/adapters/event_log/ddb.py`
- `core/gherkai_core/adapters/event_log/sqlite.py`
- `core/gherkai_core/model.py`
- `core/gherkai_core/persist.py`
- `core/gherkai_core/ports.py`
- `core/gherkai_core/project.py`
- `core/gherkai_core/reconcile.py`
- `core/gherkai_core/schedule.py`
- `core/gherkai_core/wire.py`

## Audit Trail

- EXTRACTED: 509 (71%)
- INFERRED: 205 (29%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*