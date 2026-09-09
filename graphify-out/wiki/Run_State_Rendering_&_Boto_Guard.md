# Run State Rendering & Boto Guard

> 84 nodes · cohesion 0.04

## Key Concepts

- **RunMeta** (107 connections) — `core/gherkai_core/model.py`
- **RunState** (104 connections) — `core/gherkai_core/model.py`
- **RunStore** (34 connections) — `core/gherkai_core/ports.py`
- **run_store/ddb.py** (20 connections) — `core/gherkai_core/adapters/run_store/ddb.py`
- **run_store/local.py** (20 connections) — `core/gherkai_core/adapters/run_store/local.py`
- **run_meta_from_dict()** (16 connections) — `core/gherkai_core/serialize.py`
- **run_meta_to_dict()** (16 connections) — `core/gherkai_core/serialize.py`
- **require_boto3()** (14 connections) — `core/gherkai_core/adapters/_boto.py`
- **_boto.py** (8 connections) — `core/gherkai_core/adapters/_boto.py`
- **.create_run()** (8 connections) — `core/gherkai_core/adapters/run_store/ddb.py`
- **arg_offload.py** (7 connections) — `core/gherkai_core/adapters/run_store/arg_offload.py`
- **.load_run_state()** (7 connections) — `core/gherkai_core/adapters/run_store/local.py`
- **.save_run()** (7 connections) — `core/gherkai_core/adapters/run_store/local.py`
- **._write_state()** (7 connections) — `core/gherkai_core/adapters/run_store/local.py`
- **_lifecycle_rank()** (7 connections) — `core/gherkai_core/project.py`
- **render_run_state()** (6 connections) — `cli/gherkai_cli/render.py`
- **.project_state()** (6 connections) — `core/gherkai_core/adapters/run_store/ddb.py`
- **_job_state_to_item()** (6 connections) — `core/gherkai_core/adapters/run_store/ddb.py`
- **.finalize_run()** (6 connections) — `core/gherkai_core/adapters/run_store/local.py`
- **.update_job_state()** (6 connections) — `core/gherkai_core/adapters/run_store/local.py`
- **run_state_from_dict()** (6 connections) — `core/gherkai_core/serialize.py`
- **has_pointers()** (5 connections) — `core/gherkai_core/adapters/run_store/arg_offload.py`
- **_iter_arguments()** (5 connections) — `core/gherkai_core/adapters/run_store/arg_offload.py`
- **.load_run_meta()** (5 connections) — `core/gherkai_core/adapters/run_store/ddb.py`
- **.load_run_state()** (5 connections) — `core/gherkai_core/adapters/run_store/ddb.py`
- *... and 59 more nodes in this community*

## Relationships

- [DynamoDB RunStore Conditional Writes](DynamoDB_RunStore_Conditional_Writes.md) (70 shared connections)
- [Engine Ports & Adapters](Engine_Ports_%26_Adapters.md) (43 shared connections)
- [Run Result Verdict Model](Run_Result_Verdict_Model.md) (41 shared connections)
- [SQLite Event Log & Projection](SQLite_Event_Log_%26_Projection.md) (23 shared connections)
- [Reconcile Ports & Tick](Reconcile_Ports_%26_Tick.md) (15 shared connections)
- [ResultStore Local/S3](ResultStore_Local-S3.md) (12 shared connections)
- [Cloud Launcher & DDB EventLog](Cloud_Launcher_%26_DDB_EventLog.md) (11 shared connections)
- [Conditional Write Contract Tests](Conditional_Write_Contract_Tests.md) (11 shared connections)
- [Render & ReportStore Local](Render_%26_ReportStore_Local.md) (8 shared connections)
- [Detached Launcher Reconcile](Detached_Launcher_Reconcile.md) (7 shared connections)
- [S3 ReportStore & Subprocess Engine](S3_ReportStore_%26_Subprocess_Engine.md) (6 shared connections)
- [Run Persistence Orchestration](Run_Persistence_Orchestration.md) (6 shared connections)

## Source Files

- `cli/gherkai_cli/render.py`
- `cli/tests/test_render.py`
- `core/gherkai_core/adapters/_boto.py`
- `core/gherkai_core/adapters/run_store/__init__.py`
- `core/gherkai_core/adapters/run_store/arg_offload.py`
- `core/gherkai_core/adapters/run_store/ddb.py`
- `core/gherkai_core/adapters/run_store/local.py`
- `core/gherkai_core/model.py`
- `core/gherkai_core/persist.py`
- `core/gherkai_core/ports.py`
- `core/gherkai_core/project.py`
- `core/gherkai_core/serialize.py`
- `core/tests/test_stores.py`

## Audit Trail

- EXTRACTED: 357 (84%)
- INFERRED: 69 (16%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*