# Nova Act Worker Package

> 55 nodes · cohesion 0.06

## Key Concepts

- **run_scope.py** (58 connections) — `engines/novaact/gherkai_worker_novaact/run_scope.py`
- **main()** (22 connections) — `engines/novaact/gherkai_worker_novaact/run_scope.py`
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
- **_capabilities()** (4 connections) — `engines/novaact/gherkai_worker_novaact/run_scope.py`
- **_traj_refs()** (4 connections) — `engines/novaact/gherkai_worker_novaact/run_scope.py`
- **interrupt_worker.py** (4 connections) — `engines/novaact/tests/fixtures/interrupt_worker.py`
- **test_presend_all_act_siblings()** (4 connections) — `engines/novaact/tests/test_safe_point_upload.py`
- **test_presend_swallows_upload_failure()** (4 connections) — `engines/novaact/tests/test_safe_point_upload.py`
- **test_presend_uploads_sibling_json()** (4 connections) — `engines/novaact/tests/test_safe_point_upload.py`
- **gherkai_worker_novaact/__main__.py** (3 connections) — `engines/novaact/gherkai_worker_novaact/__main__.py`
- **_cost_from_result()** (3 connections) — `engines/novaact/gherkai_worker_novaact/run_scope.py`
- *... and 30 more nodes in this community*

## Relationships

- [Step Execution Dispatch](Step_Execution_Dispatch.md) (10 shared connections)
- [Flag-only Interrupt Model](Flag-only_Interrupt_Model.md) (9 shared connections)
- [Scenario Evidence Keys](Scenario_Evidence_Keys.md) (8 shared connections)
- [Step Argument Instruction Building](Step_Argument_Instruction_Building.md) (6 shared connections)
- [Worker Main Fakes](Worker_Main_Fakes.md) (6 shared connections)
- [Transient Error Detection](Transient_Error_Detection.md) (5 shared connections)
- [Worker Event Sink](Worker_Event_Sink.md) (5 shared connections)
- [Nova Act Worker Libs](Nova_Act_Worker_Libs.md) (4 shared connections)
- [Deterministic Step Registry](Deterministic_Step_Registry.md) (3 shared connections)
- [User Steps Loading](User_Steps_Loading.md) (3 shared connections)
- [User Step Directory Loading](User_Step_Directory_Loading.md) (3 shared connections)
- [Step Evidence Extraction](Step_Evidence_Extraction.md) (3 shared connections)

## Source Files

- `engines/novaact/gherkai_worker_novaact/__init__.py`
- `engines/novaact/gherkai_worker_novaact/__main__.py`
- `engines/novaact/gherkai_worker_novaact/run_scope.py`
- `engines/novaact/tests/fixtures/interrupt_worker.py`
- `engines/novaact/tests/test_evidence.py`
- `engines/novaact/tests/test_no_artifacts.py`
- `engines/novaact/tests/test_safe_point_upload.py`

## Audit Trail

- EXTRACTED: 163 (98%)
- INFERRED: 4 (2%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*