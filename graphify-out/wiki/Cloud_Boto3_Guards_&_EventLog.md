# Cloud Boto3 Guards & EventLog

> 91 nodes · cohesion 0.04

## Key Concepts

- **Status** (105 connections) — `core/gherkai_core/model.py`
- **model.py** (78 connections) — `core/gherkai_core/model.py`
- **wire.py** (36 connections) — `core/gherkai_core/wire.py`
- **test_wire.py** (35 connections) — `core/tests/test_wire.py`
- **schedule.py** (28 connections) — `core/gherkai_core/schedule.py`
- **event_from_json()** (27 connections) — `core/gherkai_core/wire.py`
- **ports.py** (21 connections) — `core/gherkai_core/ports.py`
- **fargate_engine.py** (17 connections) — `core/gherkai_core/adapters/fargate_engine.py`
- **persist.py** (16 connections) — `core/gherkai_core/persist.py`
- **EngineResolver** (16 connections) — `core/gherkai_core/ports.py`
- **JobSink** (15 connections) — `core/gherkai_core/ports.py`
- **event_from_line()** (15 connections) — `core/gherkai_core/wire.py`
- **require_boto3()** (14 connections) — `core/gherkai_core/adapters/_boto.py`
- **Sink** (14 connections) — `core/gherkai_core/ports.py`
- **_Heartbeat** (14 connections) — `core/gherkai_core/schedule.py`
- **event_log/ddb.py** (12 connections) — `core/gherkai_core/adapters/event_log/ddb.py`
- **raise_for_worker_exit()** (12 connections) — `core/gherkai_core/wire.py`
- **Cost** (10 connections) — `core/gherkai_core/model.py`
- **job_to_json()** (9 connections) — `core/gherkai_core/wire.py`
- **job_to_line()** (9 connections) — `core/gherkai_core/wire.py`
- **_boto.py** (8 connections) — `core/gherkai_core/adapters/_boto.py`
- **sqlite.py** (8 connections) — `core/gherkai_core/adapters/event_log/sqlite.py`
- **Protocol** (8 connections)
- **arg_offload.py** (7 connections) — `core/gherkai_core/adapters/run_store/arg_offload.py`
- **_lifecycle_rank()** (7 connections) — `core/gherkai_core/project.py`
- *... and 66 more nodes in this community*

## Relationships

- [Event Formatting](Event_Formatting.md) (51 shared connections)
- [Job Explain & S3 Offload](Job_Explain_%26_S3_Offload.md) (48 shared connections)
- [DynamoDB RunStore Adapter](DynamoDB_RunStore_Adapter.md) (31 shared connections)
- [S3 Report Store & Control Plane](S3_Report_Store_%26_Control_Plane.md) (19 shared connections)
- [Schedule Core & Fakes](Schedule_Core_%26_Fakes.md) (18 shared connections)
- [S3 Result Store](S3_Result_Store.md) (16 shared connections)
- [Typed Errors & Severity](Typed_Errors_%26_Severity.md) (16 shared connections)
- [Run State Projection](Run_State_Projection.md) (14 shared connections)
- [Cloud Job Launcher](Cloud_Job_Launcher.md) (12 shared connections)
- [SQLite Event Log](SQLite_Event_Log.md) (11 shared connections)
- [Run State Rendering](Run_State_Rendering.md) (11 shared connections)
- [Text Render & Wording Guards](Text_Render_%26_Wording_Guards.md) (10 shared connections)

## Source Files

- `core/gherkai_core/adapters/_boto.py`
- `core/gherkai_core/adapters/event_log/ddb.py`
- `core/gherkai_core/adapters/event_log/sqlite.py`
- `core/gherkai_core/adapters/fargate_engine.py`
- `core/gherkai_core/adapters/run_store/arg_offload.py`
- `core/gherkai_core/adapters/run_store/ddb.py`
- `core/gherkai_core/model.py`
- `core/gherkai_core/persist.py`
- `core/gherkai_core/ports.py`
- `core/gherkai_core/project.py`
- `core/gherkai_core/schedule.py`
- `core/gherkai_core/wire.py`
- `core/tests/test_wire.py`

## Audit Trail

- EXTRACTED: 421 (83%)
- INFERRED: 88 (17%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*