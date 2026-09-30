# Nova Act Worker

> 56 nodes · cohesion 0.06

## Key Concepts

- **run_scope.py** (58 connections) — `engines/novaact/gherkai_worker_novaact/run_scope.py`
- **main()** (18 connections) — `engines/novaact/gherkai_worker_novaact/run_scope.py`
- **test_argument.py** (13 connections) — `engines/novaact/tests/test_argument.py`
- **gherkai_worker_novaact/__init__.py** (12 connections) — `engines/novaact/gherkai_worker_novaact/__init__.py`
- **_argument_text()** (10 connections) — `engines/novaact/gherkai_worker_novaact/run_scope.py`
- **_instruction()** (8 connections) — `engines/novaact/gherkai_worker_novaact/run_scope.py`
- **_attach_evidence()** (7 connections) — `engines/novaact/gherkai_worker_novaact/run_scope.py`
- **_drain_evidence_uploads()** (7 connections) — `engines/novaact/gherkai_worker_novaact/run_scope.py`
- **_emit_step_done()** (6 connections) — `engines/novaact/gherkai_worker_novaact/run_scope.py`
- **log()** (6 connections) — `engines/novaact/gherkai_worker_novaact/run_scope.py`
- **_no_artifacts()** (6 connections) — `engines/novaact/gherkai_worker_novaact/run_scope.py`
- **_collect_traj()** (5 connections) — `engines/novaact/gherkai_worker_novaact/run_scope.py`
- **_enqueue_evidence_shots()** (5 connections) — `engines/novaact/gherkai_worker_novaact/run_scope.py`
- **test_no_artifacts.py** (5 connections) — `engines/novaact/tests/test_no_artifacts.py`
- **_act_record()** (4 connections) — `engines/novaact/gherkai_worker_novaact/run_scope.py`
- **_capabilities()** (4 connections) — `engines/novaact/gherkai_worker_novaact/run_scope.py`
- **_unquote()** (4 connections) — `engines/novaact/gherkai_worker_novaact/run_scope.py`
- **interrupt_worker.py** (4 connections) — `engines/novaact/tests/fixtures/interrupt_worker.py`
- **gherkai_worker_novaact/__main__.py** (3 connections) — `engines/novaact/gherkai_worker_novaact/__main__.py`
- **_clean_cell()** (3 connections) — `engines/novaact/gherkai_worker_novaact/run_scope.py`
- **_cost_from_result()** (3 connections) — `engines/novaact/gherkai_worker_novaact/run_scope.py`
- **test_drain_noop_when_uploader_never_used()** (3 connections) — `engines/novaact/tests/test_evidence.py`
- **test_trajectory_collection_is_skipped_under_no_artifacts()** (3 connections) — `engines/novaact/tests/test_no_artifacts.py`
- **test_cell_with_newline_flattened()** (2 connections) — `engines/novaact/tests/test_argument.py`
- **test_cell_with_pipe_escaped()** (2 connections) — `engines/novaact/tests/test_argument.py`
- *... and 31 more nodes in this community*

## Relationships

- [Step Execution Dispatch](Step_Execution_Dispatch.md) (11 shared connections)
- [Interrupt and Signal Handling](Interrupt_and_Signal_Handling.md) (9 shared connections)
- [Evidence Upload Tests](Evidence_Upload_Tests.md) (8 shared connections)
- [Safe Point Upload](Safe_Point_Upload.md) (6 shared connections)
- [Nova Main Fakes](Nova_Main_Fakes.md) (6 shared connections)
- [Deterministic Step Registry](Deterministic_Step_Registry.md) (5 shared connections)
- [Transient Error Detection](Transient_Error_Detection.md) (5 shared connections)
- [User Steps Loading](User_Steps_Loading.md) (5 shared connections)
- [Nova Worker Constants and Probes](Nova_Worker_Constants_and_Probes.md) (4 shared connections)
- [Event Sink and Redaction](Event_Sink_and_Redaction.md) (4 shared connections)
- [Job Source Input](Job_Source_Input.md) (3 shared connections)
- [Step Evidence Records](Step_Evidence_Records.md) (3 shared connections)

## Source Files

- `engines/novaact/gherkai_worker_novaact/__init__.py`
- `engines/novaact/gherkai_worker_novaact/__main__.py`
- `engines/novaact/gherkai_worker_novaact/run_scope.py`
- `engines/novaact/tests/fixtures/interrupt_worker.py`
- `engines/novaact/tests/test_argument.py`
- `engines/novaact/tests/test_evidence.py`
- `engines/novaact/tests/test_no_artifacts.py`

## Audit Trail

- EXTRACTED: 155 (99%)
- INFERRED: 1 (1%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*