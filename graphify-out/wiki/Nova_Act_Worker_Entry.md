# Nova Act Worker Entry

> 45 nodes · cohesion 0.06

## Key Concepts

- **run_scope.py** (56 connections) — `engines/novaact/gherkai_worker_novaact/run_scope.py`
- **main()** (18 connections) — `engines/novaact/gherkai_worker_novaact/run_scope.py`
- **gherkai_worker_novaact/__init__.py** (12 connections) — `engines/novaact/gherkai_worker_novaact/__init__.py`
- **_DeterministicCtx** (9 connections) — `engines/novaact/gherkai_worker_novaact/run_scope.py`
- **_attach_evidence()** (7 connections) — `engines/novaact/gherkai_worker_novaact/run_scope.py`
- **_drain_evidence_uploads()** (7 connections) — `engines/novaact/gherkai_worker_novaact/run_scope.py`
- **_emit_step_done()** (6 connections) — `engines/novaact/gherkai_worker_novaact/run_scope.py`
- **_error_text()** (6 connections) — `engines/novaact/gherkai_worker_novaact/run_scope.py`
- **log()** (6 connections) — `engines/novaact/gherkai_worker_novaact/run_scope.py`
- **_no_artifacts()** (6 connections) — `engines/novaact/gherkai_worker_novaact/run_scope.py`
- **_collect_traj()** (5 connections) — `engines/novaact/gherkai_worker_novaact/run_scope.py`
- **_enqueue_evidence_shots()** (5 connections) — `engines/novaact/gherkai_worker_novaact/run_scope.py`
- **test_no_artifacts.py** (5 connections) — `engines/novaact/tests/test_no_artifacts.py`
- **_capabilities()** (4 connections) — `engines/novaact/gherkai_worker_novaact/run_scope.py`
- **_is_transient_client_error()** (4 connections) — `engines/novaact/gherkai_worker_novaact/run_scope.py`
- **BaseException** (4 connections)
- **interrupt_worker.py** (4 connections) — `engines/novaact/tests/fixtures/interrupt_worker.py`
- **gherkai_worker_novaact/__main__.py** (3 connections) — `engines/novaact/gherkai_worker_novaact/__main__.py`
- **_cost_from_result()** (3 connections) — `engines/novaact/gherkai_worker_novaact/run_scope.py`
- **test_drain_noop_when_uploader_never_used()** (3 connections) — `engines/novaact/tests/test_evidence.py`
- **test_error_text_prefers_sdk_message_and_is_single_line()** (3 connections) — `engines/novaact/tests/test_evidence.py`
- **test_trajectory_collection_is_skipped_under_no_artifacts()** (3 connections) — `engines/novaact/tests/test_no_artifacts.py`
- **test_flag_reads_env()** (2 connections) — `engines/novaact/tests/test_no_artifacts.py`
- **gherkai 的 Nova Act 引擎 worker（发行包 `gherkai-worker-novaact`，ADR 0037 决策 3）。 本包即被…** (1 connections) — `engines/novaact/gherkai_worker_novaact/__init__.py`
- **worker 进程入口（`python -m gherkai_worker_novaact`，ADR 0037 决策 3 定位链第二级）。 argv…** (1 connections) — `engines/novaact/gherkai_worker_novaact/__main__.py`
- *... and 20 more nodes in this community*

## Relationships

- [Interrupt & Termination Model](Interrupt_%26_Termination_Model.md) (11 shared connections)
- [Step Dispatch & Voting](Step_Dispatch_%26_Voting.md) (10 shared connections)
- [Evidence Artifact Upload](Evidence_Artifact_Upload.md) (9 shared connections)
- [Step Argument Assembly](Step_Argument_Assembly.md) (6 shared connections)
- [Safe-Point Trajectory Upload](Safe-Point_Trajectory_Upload.md) (6 shared connections)
- [Transient Network Detection](Transient_Network_Detection.md) (6 shared connections)
- [User Steps Loading](User_Steps_Loading.md) (6 shared connections)
- [Worker Main Fakes](Worker_Main_Fakes.md) (6 shared connections)
- [Nova Act Benchmarks & Setup](Nova_Act_Benchmarks_%26_Setup.md) (4 shared connections)
- [Deterministic Step Registry](Deterministic_Step_Registry.md) (3 shared connections)
- [Nova Event Sink](Nova_Event_Sink.md) (3 shared connections)
- [Nova Job Source](Nova_Job_Source.md) (3 shared connections)

## Source Files

- `engines/novaact/gherkai_worker_novaact/__init__.py`
- `engines/novaact/gherkai_worker_novaact/__main__.py`
- `engines/novaact/gherkai_worker_novaact/run_scope.py`
- `engines/novaact/tests/fixtures/interrupt_worker.py`
- `engines/novaact/tests/test_evidence.py`
- `engines/novaact/tests/test_no_artifacts.py`

## Audit Trail

- EXTRACTED: 137 (96%)
- INFERRED: 5 (4%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*