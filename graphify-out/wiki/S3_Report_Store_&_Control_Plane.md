# S3 Report Store & Control Plane

> 55 nodes · cohesion 0.05

## Key Concepts

- **RunStore** (34 connections) — `core/gherkai_core/ports.py`
- **ResultStore** (28 connections) — `core/gherkai_core/ports.py`
- **Engine** (22 connections) — `core/gherkai_core/ports.py`
- **ReportStore** (22 connections) — `core/gherkai_core/ports.py`
- **S3ReportStore** (18 connections) — `core/gherkai_core/adapters/report_store/s3.py`
- **_UnavailableEngine** (15 connections) — `runtime/gherkai_runtime/compose.py`
- **WorkerNotFoundError** (15 connections) — `runtime/gherkai_runtime/compose.py`
- **WorkerSelfDescribeError** (15 connections) — `runtime/gherkai_runtime/compose.py`
- **CloudTarget** (14 connections) — `runtime/gherkai_runtime/compose.py`
- **WorkerResolution** (14 connections) — `runtime/gherkai_runtime/compose.py`
- **WorkerCmd** (13 connections) — `runtime/gherkai_runtime/compose.py`
- **_ask_worker()** (9 connections) — `runtime/gherkai_runtime/compose.py`
- **.__init__()** (4 connections) — `core/gherkai_core/persist.py`
- **.__init__()** (3 connections) — `core/gherkai_core/adapters/report_store/s3.py`
- **.project_state()** (3 connections) — `core/gherkai_core/ports.py`
- **.try_finalize()** (3 connections) — `core/gherkai_core/ports.py`
- **test_prefix_lands_under_prefix()** (3 connections) — `core/tests/test_s3_report_store.py`
- **RuntimeError** (3 connections)
- **.__init__()** (3 connections) — `runtime/gherkai_runtime/compose.py`
- **.preflight()** (2 connections) — `core/gherkai_core/adapters/report_store/s3.py`
- **.__call__()** (2 connections) — `core/gherkai_core/ports.py`
- **.load_all()** (2 connections) — `core/gherkai_core/ports.py`
- **.load_job_result()** (2 connections) — `core/gherkai_core/ports.py`
- **.save_job_result()** (2 connections) — `core/gherkai_core/ports.py`
- **.finalize_run()** (2 connections) — `core/gherkai_core/ports.py`
- *... and 30 more nodes in this community*

## Relationships

- [Cloud Boto3 Guards & EventLog](Cloud_Boto3_Guards_%26_EventLog.md) (19 shared connections)
- [Job Explain & S3 Offload](Job_Explain_%26_S3_Offload.md) (17 shared connections)
- [Runtime Composition Root](Runtime_Composition_Root.md) (15 shared connections)
- [Local Report Store](Local_Report_Store.md) (9 shared connections)
- [Run State Rendering](Run_State_Rendering.md) (8 shared connections)
- [S3 Result Store](S3_Result_Store.md) (7 shared connections)
- [Text Render & Wording Guards](Text_Render_%26_Wording_Guards.md) (6 shared connections)
- [Reconciler Ports](Reconciler_Ports.md) (6 shared connections)
- [SQLite Event Log](SQLite_Event_Log.md) (6 shared connections)
- [Feature Plan to Jobs](Feature_Plan_to_Jobs.md) (6 shared connections)
- [Fargate Engine](Fargate_Engine.md) (6 shared connections)
- [DynamoDB RunStore Adapter](DynamoDB_RunStore_Adapter.md) (5 shared connections)

## Source Files

- `core/gherkai_core/adapters/report_store/s3.py`
- `core/gherkai_core/persist.py`
- `core/gherkai_core/ports.py`
- `core/tests/test_s3_report_store.py`
- `runtime/gherkai_runtime/compose.py`

## Audit Trail

- EXTRACTED: 108 (51%)
- INFERRED: 103 (49%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*