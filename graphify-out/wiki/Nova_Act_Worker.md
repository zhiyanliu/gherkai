# Nova Act Worker

> 48 nodes · cohesion 0.07

## Key Concepts

- **run_scope.py** (47 connections) — `engines/novaact/gherkai_worker_novaact/run_scope.py`
- **main()** (13 connections) — `engines/novaact/gherkai_worker_novaact/run_scope.py`
- **gherkai_worker_novaact/__init__.py** (11 connections) — `engines/novaact/gherkai_worker_novaact/__init__.py`
- **_presend_act_siblings()** (10 connections) — `engines/novaact/gherkai_worker_novaact/run_scope.py`
- **test_antetheft.py** (10 connections) — `engines/novaact/tests/test_antetheft.py`
- **_SpyUploader** (9 connections) — `engines/novaact/tests/test_antetheft.py`
- **_attach_traj_refs()** (5 connections) — `engines/novaact/gherkai_worker_novaact/run_scope.py`
- **_collect_traj()** (5 connections) — `engines/novaact/gherkai_worker_novaact/run_scope.py`
- **_get_uploader()** (5 connections) — `engines/novaact/gherkai_worker_novaact/run_scope.py`
- **_no_artifacts()** (5 connections) — `engines/novaact/gherkai_worker_novaact/run_scope.py`
- **_on_signal()** (5 connections) — `engines/novaact/gherkai_worker_novaact/run_scope.py`
- **_make_act_pair()** (5 connections) — `engines/novaact/tests/test_antetheft.py`
- **test_no_artifacts.py** (5 connections) — `engines/novaact/tests/test_no_artifacts.py`
- **_traj_refs()** (4 connections) — `engines/novaact/gherkai_worker_novaact/run_scope.py`
- **interrupt_worker.py** (4 connections) — `engines/novaact/tests/fixtures/interrupt_worker.py`
- **test_presend_all_act_siblings()** (4 connections) — `engines/novaact/tests/test_antetheft.py`
- **test_presend_swallows_upload_failure()** (4 connections) — `engines/novaact/tests/test_antetheft.py`
- **test_presend_uploads_sibling_json()** (4 connections) — `engines/novaact/tests/test_antetheft.py`
- **gherkai_worker_novaact/__main__.py** (3 connections) — `engines/novaact/gherkai_worker_novaact/__main__.py`
- **_cost_from_result()** (3 connections) — `engines/novaact/gherkai_worker_novaact/run_scope.py`
- **log()** (3 connections) — `engines/novaact/gherkai_worker_novaact/run_scope.py`
- **test_presend_ignores_non_html()** (3 connections) — `engines/novaact/tests/test_antetheft.py`
- **test_presend_skips_when_no_sibling_json()** (3 connections) — `engines/novaact/tests/test_antetheft.py`
- **test_on_signal_does_no_io_even_if_stderr_is_locked()** (3 connections) — `engines/novaact/tests/test_interrupt_model.py`
- **test_trajectory_collection_is_skipped_under_no_artifacts()** (3 connections) — `engines/novaact/tests/test_no_artifacts.py`
- *... and 23 more nodes in this community*

## Relationships

- [Worker Interrupt Model](Worker_Interrupt_Model.md) (9 shared connections)
- [Step Dispatch Execution](Step_Dispatch_Execution.md) (7 shared connections)
- [Step Argument Assembly](Step_Argument_Assembly.md) (6 shared connections)
- [Transient Error Detection](Transient_Error_Detection.md) (5 shared connections)
- [Nova Engine Probes](Nova_Engine_Probes.md) (4 shared connections)
- [User Steps Loading](User_Steps_Loading.md) (3 shared connections)
- [Worker Job Source](Worker_Job_Source.md) (3 shared connections)
- [Deterministic Step Registry](Deterministic_Step_Registry.md) (2 shared connections)
- [Worker Event Sink](Worker_Event_Sink.md) (2 shared connections)
- [Artifact S3 Upload](Artifact_S3_Upload.md) (2 shared connections)
- [Consumer Steps Directory Loading](Consumer_Steps_Directory_Loading.md) (2 shared connections)
- [Nova Deterministic Registry](Nova_Deterministic_Registry.md) (2 shared connections)

## Source Files

- `engines/novaact/gherkai_worker_novaact/__init__.py`
- `engines/novaact/gherkai_worker_novaact/__main__.py`
- `engines/novaact/gherkai_worker_novaact/run_scope.py`
- `engines/novaact/tests/fixtures/interrupt_worker.py`
- `engines/novaact/tests/test_antetheft.py`
- `engines/novaact/tests/test_interrupt_model.py`
- `engines/novaact/tests/test_no_artifacts.py`

## Audit Trail

- EXTRACTED: 124 (99%)
- INFERRED: 1 (1%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*