# Nova Act Worker Package

> 57 nodes · cohesion 0.06

## Key Concepts

- **run_scope.py** (55 connections) — `engines/novaact/gherkai_worker_novaact/run_scope.py`
- **main()** (18 connections) — `engines/novaact/gherkai_worker_novaact/run_scope.py`
- **gherkai_worker_novaact/__init__.py** (12 connections) — `engines/novaact/gherkai_worker_novaact/__init__.py`
- **_get_uploader()** (12 connections) — `engines/novaact/gherkai_worker_novaact/run_scope.py`
- **_presend_act_siblings()** (10 connections) — `engines/novaact/gherkai_worker_novaact/run_scope.py`
- **test_antetheft.py** (10 connections) — `engines/novaact/tests/test_antetheft.py`
- **_DeterministicCtx** (9 connections) — `engines/novaact/gherkai_worker_novaact/run_scope.py`
- **_SpyUploader** (9 connections) — `engines/novaact/tests/test_antetheft.py`
- **_attach_evidence()** (7 connections) — `engines/novaact/gherkai_worker_novaact/run_scope.py`
- **_drain_evidence_uploads()** (7 connections) — `engines/novaact/gherkai_worker_novaact/run_scope.py`
- **_emit_step_done()** (6 connections) — `engines/novaact/gherkai_worker_novaact/run_scope.py`
- **log()** (6 connections) — `engines/novaact/gherkai_worker_novaact/run_scope.py`
- **_no_artifacts()** (6 connections) — `engines/novaact/gherkai_worker_novaact/run_scope.py`
- **_attach_traj_refs()** (5 connections) — `engines/novaact/gherkai_worker_novaact/run_scope.py`
- **_collect_traj()** (5 connections) — `engines/novaact/gherkai_worker_novaact/run_scope.py`
- **_enqueue_evidence_shots()** (5 connections) — `engines/novaact/gherkai_worker_novaact/run_scope.py`
- **_make_act_pair()** (5 connections) — `engines/novaact/tests/test_antetheft.py`
- **test_no_artifacts.py** (5 connections) — `engines/novaact/tests/test_no_artifacts.py`
- **_traj_refs()** (4 connections) — `engines/novaact/gherkai_worker_novaact/run_scope.py`
- **interrupt_worker.py** (4 connections) — `engines/novaact/tests/fixtures/interrupt_worker.py`
- **test_presend_all_act_siblings()** (4 connections) — `engines/novaact/tests/test_antetheft.py`
- **test_presend_swallows_upload_failure()** (4 connections) — `engines/novaact/tests/test_antetheft.py`
- **test_presend_uploads_sibling_json()** (4 connections) — `engines/novaact/tests/test_antetheft.py`
- **gherkai_worker_novaact/__main__.py** (3 connections) — `engines/novaact/gherkai_worker_novaact/__main__.py`
- **_cost_from_result()** (3 connections) — `engines/novaact/gherkai_worker_novaact/run_scope.py`
- *... and 32 more nodes in this community*

## Relationships

- [Step Execution & Error Classification](Step_Execution_%26_Error_Classification.md) (11 shared connections)
- [Interrupt & Termination Model](Interrupt_%26_Termination_Model.md) (9 shared connections)
- [Scenario Key & Evidence Tests](Scenario_Key_%26_Evidence_Tests.md) (8 shared connections)
- [Worker IO Edge Components](Worker_IO_Edge_Components.md) (7 shared connections)
- [Step Argument Assembly](Step_Argument_Assembly.md) (6 shared connections)
- [Transient Error Detection](Transient_Error_Detection.md) (6 shared connections)
- [User Steps Loading](User_Steps_Loading.md) (6 shared connections)
- [Worker Main Fakes](Worker_Main_Fakes.md) (6 shared connections)
- [Deterministic Step Registry](Deterministic_Step_Registry.md) (4 shared connections)
- [Worker Job Source](Worker_Job_Source.md) (3 shared connections)
- [AWS Test Fixtures](AWS_Test_Fixtures.md) (3 shared connections)
- [Artifact Uploader (Python)](Artifact_Uploader_%28Python%29.md) (2 shared connections)

## Source Files

- `engines/novaact/gherkai_worker_novaact/__init__.py`
- `engines/novaact/gherkai_worker_novaact/__main__.py`
- `engines/novaact/gherkai_worker_novaact/run_scope.py`
- `engines/novaact/tests/fixtures/interrupt_worker.py`
- `engines/novaact/tests/test_antetheft.py`
- `engines/novaact/tests/test_evidence.py`
- `engines/novaact/tests/test_no_artifacts.py`

## Audit Trail

- EXTRACTED: 161 (97%)
- INFERRED: 5 (3%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*