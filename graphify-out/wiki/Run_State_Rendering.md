# Run State Rendering

> 74 nodes · cohesion 0.05

## Key Concepts

- **RunState** (127 connections) — `core/gherkai_core/model.py`
- **Status** (106 connections) — `core/gherkai_core/model.py`
- **JobState** (101 connections) — `core/gherkai_core/model.py`
- **model.py** (81 connections) — `core/gherkai_core/model.py`
- **RunStore** (34 connections) — `core/gherkai_core/ports.py`
- **run_store/local.py** (24 connections) — `core/gherkai_core/adapters/run_store/local.py`
- **ReportStore** (22 connections) — `core/gherkai_core/ports.py`
- **run_store/ddb.py** (20 connections) — `core/gherkai_core/adapters/run_store/ddb.py`
- **persist.py** (16 connections) — `core/gherkai_core/persist.py`
- **projected_run_status()** (10 connections) — `core/gherkai_core/project.py`
- **test_local_run_store_atomic.py** (9 connections) — `core/tests/test_local_run_store_atomic.py`
- **test_explain_cloud_not_landed_hint_carries_cloud_locator_flags()** (7 connections) — `cli/tests/test_main.py`
- **_lifecycle_rank()** (7 connections) — `core/gherkai_core/project.py`
- **render_run_state()** (6 connections) — `cli/gherkai_cli/render.py`
- **test_render_status_pending_run_with_claimed_job_does_not_hint()** (6 connections) — `cli/tests/test_main.py`
- **run_state_from_dict()** (6 connections) — `core/gherkai_core/serialize.py`
- **.load_run_state()** (5 connections) — `core/gherkai_core/adapters/run_store/ddb.py`
- **.project_state()** (5 connections) — `core/gherkai_core/adapters/run_store/ddb.py`
- **_job_state_to_item()** (5 connections) — `core/gherkai_core/adapters/run_store/ddb.py`
- **.begin()** (5 connections) — `core/gherkai_core/persist.py`
- **test_render_run_state_lists_jobs_and_session_lineage()** (4 connections) — `cli/tests/test_render.py`
- **test_render_run_state_shows_ended_at_when_terminal()** (4 connections) — `cli/tests/test_render.py`
- **.update_job_state()** (4 connections) — `core/gherkai_core/adapters/run_store/ddb.py`
- **_job_state_from_item()** (4 connections) — `core/gherkai_core/adapters/run_store/ddb.py`
- **_state_scalars()** (4 connections) — `core/gherkai_core/adapters/run_store/ddb.py`
- *... and 49 more nodes in this community*

## Relationships

- [Run Metadata & S3 Offload](Run_Metadata_%26_S3_Offload.md) (75 shared connections)
- [Local & S3 Result Stores](Local_%26_S3_Result_Stores.md) (56 shared connections)
- [S3 Result Store Port](S3_Result_Store_Port.md) (41 shared connections)
- [Event Log & Projection](Event_Log_%26_Projection.md) (41 shared connections)
- [Reconcile Orchestration](Reconcile_Orchestration.md) (23 shared connections)
- [Conditional Write Contract Tests](Conditional_Write_Contract_Tests.md) (19 shared connections)
- [Cloud Adapter Integration Tests](Cloud_Adapter_Integration_Tests.md) (15 shared connections)
- [Local Result Store](Local_Result_Store.md) (14 shared connections)
- [Explain Rendering Tests](Explain_Rendering_Tests.md) (13 shared connections)
- [Event Progress Formatting](Event_Progress_Formatting.md) (11 shared connections)
- [S3 Report Store](S3_Report_Store.md) (8 shared connections)
- [Cloud Resource Preflight](Cloud_Resource_Preflight.md) (8 shared connections)

## Source Files

- `cli/gherkai_cli/render.py`
- `cli/tests/test_main.py`
- `cli/tests/test_render.py`
- `core/gherkai_core/adapters/run_store/__init__.py`
- `core/gherkai_core/adapters/run_store/ddb.py`
- `core/gherkai_core/adapters/run_store/local.py`
- `core/gherkai_core/model.py`
- `core/gherkai_core/persist.py`
- `core/gherkai_core/ports.py`
- `core/gherkai_core/project.py`
- `core/gherkai_core/serialize.py`
- `core/tests/test_ddb_run_store.py`
- `core/tests/test_local_run_store_atomic.py`
- `core/tests/test_project.py`

## Audit Trail

- EXTRACTED: 437 (76%)
- INFERRED: 137 (24%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*