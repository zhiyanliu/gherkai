# Nova Act Worker Runtime

> 52 nodes · cohesion 0.06

## Key Concepts

- **run_scope.py** (58 connections) — `engines/novaact/gherkai_worker_novaact/run_scope.py`
- **gherkai_worker_novaact/__init__.py** (12 connections) — `engines/novaact/gherkai_worker_novaact/__init__.py`
- **_get_uploader()** (12 connections) — `engines/novaact/gherkai_worker_novaact/run_scope.py`
- **_presend_act_siblings()** (10 connections) — `engines/novaact/gherkai_worker_novaact/run_scope.py`
- **test_safe_point_upload.py** (10 connections) — `engines/novaact/tests/test_safe_point_upload.py`
- **_SpyUploader** (9 connections) — `engines/novaact/tests/test_safe_point_upload.py`
- **_attach_evidence()** (7 connections) — `engines/novaact/gherkai_worker_novaact/run_scope.py`
- **_drain_evidence_uploads()** (7 connections) — `engines/novaact/gherkai_worker_novaact/run_scope.py`
- **_emit_step_done()** (6 connections) — `engines/novaact/gherkai_worker_novaact/run_scope.py`
- **log()** (6 connections) — `engines/novaact/gherkai_worker_novaact/run_scope.py`
- **_no_artifacts()** (6 connections) — `engines/novaact/gherkai_worker_novaact/run_scope.py`
- **_attach_traj_refs()** (5 connections) — `engines/novaact/gherkai_worker_novaact/run_scope.py`
- **_collect_traj()** (5 connections) — `engines/novaact/gherkai_worker_novaact/run_scope.py`
- **_enqueue_evidence_shots()** (5 connections) — `engines/novaact/gherkai_worker_novaact/run_scope.py`
- **test_no_artifacts.py** (5 connections) — `engines/novaact/tests/test_no_artifacts.py`
- **_make_act_pair()** (5 connections) — `engines/novaact/tests/test_safe_point_upload.py`
- **_act_record()** (4 connections) — `engines/novaact/gherkai_worker_novaact/run_scope.py`
- **_traj_refs()** (4 connections) — `engines/novaact/gherkai_worker_novaact/run_scope.py`
- **interrupt_worker.py** (4 connections) — `engines/novaact/tests/fixtures/interrupt_worker.py`
- **test_presend_all_act_siblings()** (4 connections) — `engines/novaact/tests/test_safe_point_upload.py`
- **test_presend_swallows_upload_failure()** (4 connections) — `engines/novaact/tests/test_safe_point_upload.py`
- **test_presend_uploads_sibling_json()** (4 connections) — `engines/novaact/tests/test_safe_point_upload.py`
- **_cost_from_result()** (3 connections) — `engines/novaact/gherkai_worker_novaact/run_scope.py`
- **test_drain_noop_when_uploader_never_used()** (3 connections) — `engines/novaact/tests/test_evidence.py`
- **test_trajectory_collection_is_skipped_under_no_artifacts()** (3 connections) — `engines/novaact/tests/test_no_artifacts.py`
- *... and 27 more nodes in this community*

## Relationships

- [Step and Scenario Execution](Step_and_Scenario_Execution.md) (11 shared connections)
- [Nova Worker Process Entry](Nova_Worker_Process_Entry.md) (9 shared connections)
- [Scenario Evidence Keys](Scenario_Evidence_Keys.md) (8 shared connections)
- [Step Argument Assembly](Step_Argument_Assembly.md) (6 shared connections)
- [Interrupt and Signal Handling](Interrupt_and_Signal_Handling.md) (6 shared connections)
- [Worker Event Sink](Worker_Event_Sink.md) (5 shared connections)
- [Transient Error Detection](Transient_Error_Detection.md) (4 shared connections)
- [Nova Worker Library Setup](Nova_Worker_Library_Setup.md) (3 shared connections)
- [CLI Test Fixtures](CLI_Test_Fixtures.md) (3 shared connections)
- [User Steps Directory Loading](User_Steps_Directory_Loading.md) (2 shared connections)
- [Worker Job Source](Worker_Job_Source.md) (2 shared connections)
- [User Step Loading](User_Step_Loading.md) (2 shared connections)

## Source Files

- `engines/novaact/gherkai_worker_novaact/__init__.py`
- `engines/novaact/gherkai_worker_novaact/run_scope.py`
- `engines/novaact/tests/fixtures/interrupt_worker.py`
- `engines/novaact/tests/test_evidence.py`
- `engines/novaact/tests/test_no_artifacts.py`
- `engines/novaact/tests/test_safe_point_upload.py`

## Audit Trail

- EXTRACTED: 150 (100%)
- INFERRED: 0 (0%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*