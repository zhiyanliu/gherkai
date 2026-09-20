# S3 Result Store Port

> 74 nodes · cohesion 0.05

## Key Concepts

- **JobResult** (83 connections) — `core/gherkai_core/model.py`
- **ports.py** (29 connections) — `core/gherkai_core/ports.py`
- **ResultStore** (28 connections) — `core/gherkai_core/ports.py`
- **schedule.py** (28 connections) — `core/gherkai_core/schedule.py`
- **Engine** (22 connections) — `core/gherkai_core/ports.py`
- **_Worker** (21 connections) — `core/gherkai_core/schedule.py`
- **S3ResultStore** (17 connections) — `core/gherkai_core/adapters/result_store/s3.py`
- **EngineResolver** (16 connections) — `core/gherkai_core/ports.py`
- **JobSink** (15 connections) — `core/gherkai_core/ports.py`
- **test_s3_result_store.py** (15 connections) — `core/tests/test_s3_result_store.py`
- **Sink** (14 connections) — `core/gherkai_core/ports.py`
- **_Heartbeat** (14 connections) — `core/gherkai_core/schedule.py`
- **_job_def()** (14 connections) — `core/tests/test_stores.py`
- **WorkerHandle** (12 connections) — `core/gherkai_core/ports.py`
- **reduce_event()** (11 connections) — `core/gherkai_core/project.py`
- **._run_once()** (9 connections) — `core/gherkai_core/schedule.py`
- **Protocol** (8 connections)
- **._reduce()** (6 connections) — `core/gherkai_core/schedule.py`
- **.load_all()** (5 connections) — `core/gherkai_core/adapters/result_store/s3.py`
- **.load_job_result()** (5 connections) — `core/gherkai_core/adapters/result_store/s3.py`
- **.save_job_result()** (5 connections) — `core/gherkai_core/adapters/result_store/s3.py`
- **.run_scope()** (5 connections) — `core/gherkai_core/ports.py`
- **test_result_store_scope_id_not_path_traversal()** (5 connections) — `core/tests/test_stores.py`
- **._key()** (4 connections) — `core/gherkai_core/adapters/result_store/s3.py`
- **.run()** (4 connections) — `core/gherkai_core/schedule.py`
- *... and 49 more nodes in this community*

## Relationships

- [Run State Rendering](Run_State_Rendering.md) (41 shared connections)
- [Run Metadata & S3 Offload](Run_Metadata_%26_S3_Offload.md) (26 shared connections)
- [Explain Rendering Tests](Explain_Rendering_Tests.md) (22 shared connections)
- [Local & S3 Result Stores](Local_%26_S3_Result_Stores.md) (21 shared connections)
- [Event Log & Projection](Event_Log_%26_Projection.md) (16 shared connections)
- [Local Result Store](Local_Result_Store.md) (11 shared connections)
- [Run Scheduling Core](Run_Scheduling_Core.md) (11 shared connections)
- [Core Typed Errors](Core_Typed_Errors.md) (7 shared connections)
- [Event Progress Formatting](Event_Progress_Formatting.md) (7 shared connections)
- [SSM Paths & Composition Root](SSM_Paths_%26_Composition_Root.md) (6 shared connections)
- [Reconcile Orchestration](Reconcile_Orchestration.md) (6 shared connections)
- [S3 Report Store](S3_Report_Store.md) (6 shared connections)

## Source Files

- `CONTEXT.md`
- `core/DEVELOPMENT.md`
- `core/gherkai_core/adapters/result_store/s3.py`
- `core/gherkai_core/model.py`
- `core/gherkai_core/ports.py`
- `core/gherkai_core/project.py`
- `core/gherkai_core/schedule.py`
- `core/tests/test_s3_result_store.py`
- `core/tests/test_stores.py`

## Audit Trail

- EXTRACTED: 239 (70%)
- INFERRED: 103 (30%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*