# Nova Act Worker Entry

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

- [Step Execution & Error Classification](Step_Execution_%26_Error_Classification.md) (10 shared connections)
- [Scenario Evidence Tests](Scenario_Evidence_Tests.md) (9 shared connections)
- [Interrupt & Signal Handling](Interrupt_%26_Signal_Handling.md) (9 shared connections)
- [Deterministic Step Loading](Deterministic_Step_Loading.md) (7 shared connections)
- [Step Argument Formatting](Step_Argument_Formatting.md) (6 shared connections)
- [Worker Main Fakes](Worker_Main_Fakes.md) (6 shared connections)
- [Transient Error Detection](Transient_Error_Detection.md) (5 shared connections)
- [Worker Event Sink & Redaction](Worker_Event_Sink_%26_Redaction.md) (5 shared connections)
- [Deterministic Step Registry](Deterministic_Step_Registry.md) (4 shared connections)
- [Nova Act Workflow & Probes](Nova_Act_Workflow_%26_Probes.md) (4 shared connections)
- [Step Evidence Records](Step_Evidence_Records.md) (3 shared connections)
- [Worker Job Source Input](Worker_Job_Source_Input.md) (2 shared connections)

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