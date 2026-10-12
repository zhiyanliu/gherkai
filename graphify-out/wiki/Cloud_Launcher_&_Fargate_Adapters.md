# Cloud Launcher & Fargate Adapters

> 136 nodes · cohesion 0.03

## Key Concepts

- **RunMeta** (120 connections) — `core/gherkai_core/model.py`
- **Status** (106 connections) — `core/gherkai_core/model.py`
- **model.py** (80 connections) — `core/gherkai_core/model.py`
- **project.py** (41 connections) — `core/gherkai_core/project.py`
- **RunStore** (34 connections) — `core/gherkai_core/ports.py`
- **FargateEngine** (31 connections) — `core/gherkai_core/adapters/fargate_engine.py`
- **ports.py** (28 connections) — `core/gherkai_core/ports.py`
- **ResultStore** (28 connections) — `core/gherkai_core/ports.py`
- **schedule.py** (28 connections) — `core/gherkai_core/schedule.py`
- **WorkerVariantError** (26 connections) — `runtime/gherkai_runtime/compose.py`
- **Timing** (24 connections) — `core/gherkai_core/project.py`
- **Engine** (22 connections) — `core/gherkai_core/ports.py`
- **ReportStore** (22 connections) — `core/gherkai_core/ports.py`
- **NonTerminalSnapshot** (21 connections) — `core/gherkai_core/project.py`
- **_Worker** (21 connections) — `core/gherkai_core/schedule.py`
- **fargate_engine.py** (20 connections) — `core/gherkai_core/adapters/fargate_engine.py`
- **run_store/ddb.py** (20 connections) — `core/gherkai_core/adapters/run_store/ddb.py`
- **S3ReportStore** (18 connections) — `core/gherkai_core/adapters/report_store/s3.py`
- **persist.py** (17 connections) — `core/gherkai_core/persist.py`
- **reconcile.py** (17 connections) — `core/gherkai_core/reconcile.py`
- **EngineResolver** (16 connections) — `core/gherkai_core/ports.py`
- **JobSink** (15 connections) — `core/gherkai_core/ports.py`
- **_UnavailableEngine** (15 connections) — `runtime/gherkai_runtime/compose.py`
- **WorkerNotFoundError** (15 connections) — `runtime/gherkai_runtime/compose.py`
- **WorkerSelfDescribeError** (15 connections) — `runtime/gherkai_runtime/compose.py`
- *... and 111 more nodes in this community*

## Relationships

- [Job/Scenario Explain Model](Job-Scenario_Explain_Model.md) (85 shared connections)
- [Fake DDB Table & SQLite Records](Fake_DDB_Table_%26_SQLite_Records.md) (45 shared connections)
- [Result Rendering & Explain](Result_Rendering_%26_Explain.md) (39 shared connections)
- [Job State Serialization](Job_State_Serialization.md) (37 shared connections)
- [S3 Result Store](S3_Result_Store.md) (34 shared connections)
- [Run State Rendering & DDB Store](Run_State_Rendering_%26_DDB_Store.md) (34 shared connections)
- [Event Progress Formatting](Event_Progress_Formatting.md) (32 shared connections)
- [SQLite Event Log Adapter](SQLite_Event_Log_Adapter.md) (32 shared connections)
- [Schedule Module Tests](Schedule_Module_Tests.md) (19 shared connections)
- [Reconcile Tick & Report Finalize](Reconcile_Tick_%26_Report_Finalize.md) (17 shared connections)
- [Cloud Store Composition Root](Cloud_Store_Composition_Root.md) (15 shared connections)
- [Local Result Store & Persistence](Local_Result_Store_%26_Persistence.md) (13 shared connections)

## Source Files

- `core/DEVELOPMENT.md`
- `core/README.md`
- `core/gherkai_core/adapters/cloud_launcher.py`
- `core/gherkai_core/adapters/fargate_engine.py`
- `core/gherkai_core/adapters/report_store/s3.py`
- `core/gherkai_core/adapters/run_store/ddb.py`
- `core/gherkai_core/model.py`
- `core/gherkai_core/persist.py`
- `core/gherkai_core/ports.py`
- `core/gherkai_core/project.py`
- `core/gherkai_core/reconcile.py`
- `core/gherkai_core/schedule.py`
- `runtime/gherkai_runtime/compose.py`

## Audit Trail

- EXTRACTED: 574 (68%)
- INFERRED: 274 (32%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*