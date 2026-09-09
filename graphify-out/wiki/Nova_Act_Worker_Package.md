# Nova Act Worker Package

> 36 nodes · cohesion 0.08

## Key Concepts

- **run_scope.py** (47 connections) — `engines/novaact/gherkai_worker_novaact/run_scope.py`
- **main()** (13 connections) — `engines/novaact/gherkai_worker_novaact/run_scope.py`
- **gherkai_worker_novaact/__init__.py** (11 connections) — `engines/novaact/gherkai_worker_novaact/__init__.py`
- **_attach_traj_refs()** (5 connections) — `engines/novaact/gherkai_worker_novaact/run_scope.py`
- **_backoff_interrupted()** (5 connections) — `engines/novaact/gherkai_worker_novaact/run_scope.py`
- **_collect_traj()** (5 connections) — `engines/novaact/gherkai_worker_novaact/run_scope.py`
- **_get_uploader()** (5 connections) — `engines/novaact/gherkai_worker_novaact/run_scope.py`
- **_no_artifacts()** (5 connections) — `engines/novaact/gherkai_worker_novaact/run_scope.py`
- **_on_signal()** (5 connections) — `engines/novaact/gherkai_worker_novaact/run_scope.py`
- **test_no_artifacts.py** (5 connections) — `engines/novaact/tests/test_no_artifacts.py`
- **_traj_refs()** (4 connections) — `engines/novaact/gherkai_worker_novaact/run_scope.py`
- **interrupt_worker.py** (4 connections) — `engines/novaact/tests/fixtures/interrupt_worker.py`
- **gherkai_worker_novaact/__main__.py** (3 connections) — `engines/novaact/gherkai_worker_novaact/__main__.py`
- **_cost_from_result()** (3 connections) — `engines/novaact/gherkai_worker_novaact/run_scope.py`
- **log()** (3 connections) — `engines/novaact/gherkai_worker_novaact/run_scope.py`
- **test_trajectory_collection_is_skipped_under_no_artifacts()** (3 connections) — `engines/novaact/tests/test_no_artifacts.py`
- **test_backoff_interrupted_times_out_without_stop()** (2 connections) — `engines/novaact/tests/test_interrupt_model.py`
- **test_backoff_interrupted_wakes_on_stop()** (2 connections) — `engines/novaact/tests/test_interrupt_model.py`
- **test_signal_handler_only_sets_flag_never_raises()** (2 connections) — `engines/novaact/tests/test_interrupt_model.py`
- **test_sigterm_and_sigint_both_installed_as_flag_only()** (2 connections) — `engines/novaact/tests/test_interrupt_model.py`
- **test_flag_reads_env()** (2 connections) — `engines/novaact/tests/test_no_artifacts.py`
- **ArtifactUploader** (1 connections)
- **gherkai 的 Nova Act 引擎 worker（发行包 `gherkai-worker-novaact`，ADR 0037 决策 3）。 本包 =…** (1 connections) — `engines/novaact/gherkai_worker_novaact/__init__.py`
- **worker 进程入口（`python -m gherkai_worker_novaact`，ADR 0037 决策 3 定位链第二级）。 argv…** (1 connections) — `engines/novaact/gherkai_worker_novaact/__main__.py`
- **Nova Act 薄 worker（ADR 0022/0024）：读入一个 scope 的 job JSON → 跑这个 scope → 吐 ADR 0024…** (1 connections) — `engines/novaact/gherkai_worker_novaact/run_scope.py`
- *... and 11 more nodes in this community*

## Relationships

- [Worker Interrupt Model](Worker_Interrupt_Model.md) (9 shared connections)
- [Step Dispatch & Error Mapping](Step_Dispatch_%26_Error_Mapping.md) (8 shared connections)
- [Act Boundary Presend Upload](Act_Boundary_Presend_Upload.md) (6 shared connections)
- [Step Argument Assembly](Step_Argument_Assembly.md) (6 shared connections)
- [Transient Error Classification](Transient_Error_Classification.md) (5 shared connections)
- [Deterministic Step Registry](Deterministic_Step_Registry.md) (4 shared connections)
- [Nova Workflow Setup & Probes](Nova_Workflow_Setup_%26_Probes.md) (4 shared connections)
- [User Steps Directory Loading](User_Steps_Directory_Loading.md) (3 shared connections)
- [Job Source Input](Job_Source_Input.md) (3 shared connections)
- [Worker Event Sink](Worker_Event_Sink.md) (2 shared connections)
- [Artifact S3 Upload](Artifact_S3_Upload.md) (2 shared connections)
- [User Steps Directory Loader](User_Steps_Directory_Loader.md) (2 shared connections)

## Source Files

- `engines/novaact/gherkai_worker_novaact/__init__.py`
- `engines/novaact/gherkai_worker_novaact/__main__.py`
- `engines/novaact/gherkai_worker_novaact/run_scope.py`
- `engines/novaact/tests/fixtures/interrupt_worker.py`
- `engines/novaact/tests/test_interrupt_model.py`
- `engines/novaact/tests/test_no_artifacts.py`

## Audit Trail

- EXTRACTED: 102 (99%)
- INFERRED: 1 (1%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*