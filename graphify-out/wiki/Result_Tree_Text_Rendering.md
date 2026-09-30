# Result Tree Text Rendering

> 94 nodes · cohesion 0.05

## Key Concepts

- **Status** (97 connections) — `core/gherkai_core/model.py`
- **JobResult** (82 connections) — `core/gherkai_core/model.py`
- **RunResult** (63 connections) — `core/gherkai_core/model.py`
- **project.py** (41 connections) — `core/gherkai_core/project.py`
- **StepResult** (36 connections) — `core/gherkai_core/model.py`
- **ScenarioResult** (34 connections) — `core/gherkai_core/model.py`
- **schedule.py** (30 connections) — `core/gherkai_core/schedule.py`
- **Timing** (24 connections) — `core/gherkai_core/project.py`
- **NonTerminalSnapshot** (21 connections) — `core/gherkai_core/project.py`
- **_Worker** (21 connections) — `core/gherkai_core/schedule.py`
- **test_render.py** (20 connections) — `cli/tests/test_render.py`
- **EngineResolver** (16 connections) — `core/gherkai_core/ports.py`
- **JobSink** (15 connections) — `core/gherkai_core/ports.py`
- **Sink** (14 connections) — `core/gherkai_core/ports.py`
- **_Heartbeat** (14 connections) — `core/gherkai_core/schedule.py`
- **render_text()** (13 connections) — `cli/gherkai_cli/render.py`
- **test_explain_cloud_reads_evidence_from_s3()** (13 connections) — `cli/tests/test_main.py`
- **Engine** (12 connections) — `core/gherkai_core/ports.py`
- **WorkerHandle** (12 connections) — `core/gherkai_core/ports.py`
- **_aggregate()** (12 connections) — `core/gherkai_core/project.py`
- **_sample_run()** (11 connections) — `cli/tests/test_render.py`
- **reduce_event()** (11 connections) — `core/gherkai_core/project.py`
- **_reduce_scope()** (11 connections) — `core/gherkai_core/project.py`
- **test_run_tree_attaches_reason_and_refs_under_their_step()** (10 connections) — `cli/tests/test_render.py`
- **test_index_html_shortcircuit_note_matches_cli_wording()** (9 connections) — `cli/tests/test_render.py`
- *... and 69 more nodes in this community*

## Relationships

- [Worker Log Event Formatting](Worker_Log_Event_Formatting.md) (57 shared connections)
- [Run Definition Domain Model](Run_Definition_Domain_Model.md) (49 shared connections)
- [Core Adapters Documentation](Core_Adapters_Documentation.md) (44 shared connections)
- [Report Store Adapters](Report_Store_Adapters.md) (35 shared connections)
- [Run State Rendering](Run_State_Rendering.md) (30 shared connections)
- [Event Records Projection](Event_Records_Projection.md) (28 shared connections)
- [Run Persistence Orchestration](Run_Persistence_Orchestration.md) (21 shared connections)
- [Result Store Serialization](Result_Store_Serialization.md) (19 shared connections)
- [DynamoDB Run Store](DynamoDB_Run_Store.md) (16 shared connections)
- [S3 Result Store](S3_Result_Store.md) (12 shared connections)
- [Atomic Local Writes](Atomic_Local_Writes.md) (8 shared connections)
- [Reconciler Plan Next](Reconciler_Plan_Next.md) (7 shared connections)

## Source Files

- `cli/gherkai_cli/render.py`
- `cli/tests/test_main.py`
- `cli/tests/test_render.py`
- `core/gherkai_core/adapters/run_store/ddb.py`
- `core/gherkai_core/model.py`
- `core/gherkai_core/ports.py`
- `core/gherkai_core/project.py`
- `core/gherkai_core/schedule.py`
- `core/tests/test_lifecycle_states.py`

## Audit Trail

- EXTRACTED: 438 (73%)
- INFERRED: 163 (27%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*