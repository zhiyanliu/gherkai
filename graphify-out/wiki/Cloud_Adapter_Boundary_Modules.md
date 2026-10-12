# Cloud Adapter Boundary Modules

> 93 nodes · cohesion 0.04

## Key Concepts

- **Status** (106 connections) — `core/gherkai_core/model.py`
- **model.py** (80 connections) — `core/gherkai_core/model.py`
- **project.py** (41 connections) — `core/gherkai_core/project.py`
- **ScopeDone** (40 connections) — `core/gherkai_core/model.py`
- **wire.py** (38 connections) — `core/gherkai_core/wire.py`
- **TaskExited** (29 connections) — `core/gherkai_core/project.py`
- **ports.py** (28 connections) — `core/gherkai_core/ports.py`
- **schedule.py** (28 connections) — `core/gherkai_core/schedule.py`
- **Timing** (24 connections) — `core/gherkai_core/project.py`
- **NonTerminalSnapshot** (21 connections) — `core/gherkai_core/project.py`
- **_Worker** (21 connections) — `core/gherkai_core/schedule.py`
- **fargate_engine.py** (20 connections) — `core/gherkai_core/adapters/fargate_engine.py`
- **persist.py** (17 connections) — `core/gherkai_core/persist.py`
- **reconcile.py** (17 connections) — `core/gherkai_core/reconcile.py`
- **StepSkipped** (16 connections) — `core/gherkai_core/model.py`
- **EngineResolver** (16 connections) — `core/gherkai_core/ports.py`
- **StepStarted** (15 connections) — `core/gherkai_core/model.py`
- **JobSink** (15 connections) — `core/gherkai_core/ports.py`
- **Sink** (14 connections) — `core/gherkai_core/ports.py`
- **_Heartbeat** (14 connections) — `core/gherkai_core/schedule.py`
- **event_log/ddb.py** (12 connections) — `core/gherkai_core/adapters/event_log/ddb.py`
- **errors.py** (12 connections) — `core/gherkai_core/errors.py`
- **reduce_event()** (11 connections) — `core/gherkai_core/project.py`
- **_reduce_scope()** (11 connections) — `core/gherkai_core/project.py`
- **projected_run_status()** (10 connections) — `core/gherkai_core/project.py`
- *... and 68 more nodes in this community*

## Relationships

- [Run Scheduling Events Core](Run_Scheduling_Events_Core.md) (63 shared connections)
- [Job Explain Data Model](Job_Explain_Data_Model.md) (48 shared connections)
- [Reconciler Event Projection](Reconciler_Event_Projection.md) (47 shared connections)
- [Run State Store](Run_State_Store.md) (28 shared connections)
- [DynamoDB Job State Store](DynamoDB_Job_State_Store.md) (24 shared connections)
- [S3 Result Store](S3_Result_Store.md) (21 shared connections)
- [Event Wire Protocol](Event_Wire_Protocol.md) (19 shared connections)
- [Terminal State Aggregation](Terminal_State_Aggregation.md) (19 shared connections)
- [Explain Reads And Report Store](Explain_Reads_And_Report_Store.md) (16 shared connections)
- [Result Tree Rendering](Result_Tree_Rendering.md) (14 shared connections)
- [Step Argument S3 Offload](Step_Argument_S3_Offload.md) (10 shared connections)
- [EventLog And Launcher Ports](EventLog_And_Launcher_Ports.md) (10 shared connections)

## Source Files

- `core/DEVELOPMENT.md`
- `core/README.md`
- `core/gherkai_core/adapters/_boto.py`
- `core/gherkai_core/adapters/cloud_launcher.py`
- `core/gherkai_core/adapters/event_log/ddb.py`
- `core/gherkai_core/adapters/event_log/sqlite.py`
- `core/gherkai_core/adapters/fargate_engine.py`
- `core/gherkai_core/adapters/run_store/ddb.py`
- `core/gherkai_core/errors.py`
- `core/gherkai_core/model.py`
- `core/gherkai_core/persist.py`
- `core/gherkai_core/ports.py`
- `core/gherkai_core/project.py`
- `core/gherkai_core/reconcile.py`
- `core/gherkai_core/schedule.py`
- `core/gherkai_core/wire.py`

## Audit Trail

- EXTRACTED: 480 (75%)
- INFERRED: 161 (25%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*