# Run State Store

> 62 nodes · cohesion 0.05

## Key Concepts

- **RunState** (127 connections) — `core/gherkai_core/model.py`
- **LocalRunStore** (53 connections) — `core/gherkai_core/adapters/run_store/local.py`
- **RunStore** (34 connections) — `core/gherkai_core/ports.py`
- **run_store/local.py** (24 connections) — `core/gherkai_core/adapters/run_store/local.py`
- **test_local_run_store_atomic.py** (9 connections) — `core/tests/test_local_run_store_atomic.py`
- **.save_run()** (8 connections) — `core/gherkai_core/adapters/run_store/local.py`
- **._write_state()** (8 connections) — `core/gherkai_core/adapters/run_store/local.py`
- **test_explain_cloud_not_landed_hint_carries_cloud_locator_flags()** (7 connections) — `cli/tests/test_main.py`
- **.load_run_state()** (7 connections) — `core/gherkai_core/adapters/run_store/local.py`
- **._locked_rmw()** (7 connections) — `core/gherkai_core/adapters/run_store/local.py`
- **test_render_status_pending_run_with_claimed_job_does_not_hint()** (6 connections) — `cli/tests/test_main.py`
- **_atomic_write_json()** (6 connections) — `core/gherkai_core/adapters/run_store/local.py`
- **.finalize_run()** (6 connections) — `core/gherkai_core/adapters/run_store/local.py`
- **.update_job_state()** (6 connections) — `core/gherkai_core/adapters/run_store/local.py`
- **run_state_from_dict()** (6 connections) — `core/gherkai_core/serialize.py`
- **run_state_to_dict()** (6 connections) — `core/gherkai_core/serialize.py`
- **.create_run()** (5 connections) — `core/gherkai_core/adapters/run_store/local.py`
- **.begin()** (5 connections) — `core/gherkai_core/persist.py`
- **_state_scalars()** (4 connections) — `core/gherkai_core/adapters/run_store/ddb.py`
- **.load_run_meta()** (4 connections) — `core/gherkai_core/adapters/run_store/local.py`
- **.project_state()** (4 connections) — `core/gherkai_core/adapters/run_store/local.py`
- **.try_finalize()** (4 connections) — `core/gherkai_core/adapters/run_store/local.py`
- **_big_state()** (4 connections) — `core/tests/test_local_run_store_atomic.py`
- **run_store/__init__.py** (3 connections) — `core/gherkai_core/adapters/run_store/__init__.py`
- **.try_claim_job()** (3 connections) — `core/gherkai_core/adapters/run_store/local.py`
- *... and 37 more nodes in this community*

## Relationships

- [Job Explain Data Model](Job_Explain_Data_Model.md) (39 shared connections)
- [DynamoDB Job State Store](DynamoDB_Job_State_Store.md) (36 shared connections)
- [Cloud Adapter Boundary Modules](Cloud_Adapter_Boundary_Modules.md) (28 shared connections)
- [EventLog And Launcher Ports](EventLog_And_Launcher_Ports.md) (12 shared connections)
- [Conditional Write Guards](Conditional_Write_Guards.md) (12 shared connections)
- [Run Persistence Local Stores](Run_Persistence_Local_Stores.md) (9 shared connections)
- [Store Port Definitions](Store_Port_Definitions.md) (8 shared connections)
- [Local Reconcile Rebuild](Local_Reconcile_Rebuild.md) (7 shared connections)
- [Lambda Handler Event Parsing Tests](Lambda_Handler_Event_Parsing_Tests.md) (6 shared connections)
- [Reconciler Event Projection](Reconciler_Event_Projection.md) (6 shared connections)
- [Timestamp & Wallclock Utils](Timestamp_%26_Wallclock_Utils.md) (5 shared connections)
- [Result Store Adapters](Result_Store_Adapters.md) (4 shared connections)

## Source Files

- `cli/tests/test_main.py`
- `core/gherkai_core/adapters/run_store/__init__.py`
- `core/gherkai_core/adapters/run_store/ddb.py`
- `core/gherkai_core/adapters/run_store/local.py`
- `core/gherkai_core/model.py`
- `core/gherkai_core/persist.py`
- `core/gherkai_core/ports.py`
- `core/gherkai_core/serialize.py`
- `core/tests/test_local_run_store_atomic.py`

## Audit Trail

- EXTRACTED: 257 (82%)
- INFERRED: 55 (18%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*