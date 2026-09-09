# Nova Workflow Setup & Probes

> 34 nodes · cohesion 0.10

## Key Concepts

- **ensure_workflow_definition()** (12 connections) — `engines/novaact/gherkai_worker_novaact/lib/workflow_setup.py`
- **_FakeNovaActClient** (12 connections) — `engines/novaact/tests/test_workflow_setup.py`
- **test_workflow_setup.py** (10 connections) — `engines/novaact/tests/test_workflow_setup.py`
- **_patch()** (7 connections) — `engines/novaact/tests/test_workflow_setup.py`
- **workflow_setup.py** (6 connections) — `engines/novaact/gherkai_worker_novaact/lib/workflow_setup.py`
- **negative_assertions.py** (5 connections) — `engines/novaact/spikes/negative_assertions.py`
- **wikipedia_benchmark.py** (5 connections) — `engines/novaact/spikes/wikipedia_benchmark.py`
- **test_concurrent_create_conflict_counts_as_exists()** (5 connections) — `engines/novaact/tests/test_workflow_setup.py`
- **test_other_create_error_propagates()** (5 connections) — `engines/novaact/tests/test_workflow_setup.py`
- **constants.py** (4 connections) — `engines/novaact/gherkai_worker_novaact/lib/constants.py`
- **test_create_omits_description_when_absent()** (4 connections) — `engines/novaact/tests/test_workflow_setup.py`
- **test_exists_short_circuits_without_create()** (4 connections) — `engines/novaact/tests/test_workflow_setup.py`
- **test_missing_definition_is_created()** (4 connections) — `engines/novaact/tests/test_workflow_setup.py`
- **exceptions** (3 connections) — `engines/novaact/tests/test_workflow_setup.py`
- **Exception** (3 connections)
- **lib/__init__.py** (2 connections) — `engines/novaact/gherkai_worker_novaact/lib/__init__.py`
- **main()** (2 connections) — `engines/novaact/spikes/negative_assertions.py`
- **run()** (2 connections) — `engines/novaact/spikes/wikipedia_benchmark.py`
- **ConflictException** (2 connections) — `engines/novaact/tests/test_workflow_setup.py`
- **.__init__()** (2 connections) — `engines/novaact/tests/test_workflow_setup.py`
- **ResourceNotFoundException** (2 connections) — `engines/novaact/tests/test_workflow_setup.py`
- **Nova Act 引擎的共享常量（单一真理源）。 生产 worker（本包 `run_scope.py`）与 spike 脚本（repo 里的…** (1 connections) — `engines/novaact/gherkai_worker_novaact/lib/constants.py`
- **worker 的 I/O 边缘组件（ADR 0024「I/O 边缘可注入接口」）。 `job_source` / `event_sink` /…** (1 connections) — `engines/novaact/gherkai_worker_novaact/lib/__init__.py`
- **Nova Act workflow definition 的 create-if-not-exists（端到端闭环，无需手动 CLI）。 @workflow…** (1 connections) — `engines/novaact/gherkai_worker_novaact/lib/workflow_setup.py`
- **确保名为 `name` 的 workflow definition 存在；返回 'exists' 或 'created'。 并发档也幂等（ADR…** (1 connections) — `engines/novaact/gherkai_worker_novaact/lib/workflow_setup.py`
- *... and 9 more nodes in this community*

## Relationships

- [Nova Act Worker Package](Nova_Act_Worker_Package.md) (4 shared connections)

## Source Files

- `engines/novaact/gherkai_worker_novaact/lib/__init__.py`
- `engines/novaact/gherkai_worker_novaact/lib/constants.py`
- `engines/novaact/gherkai_worker_novaact/lib/workflow_setup.py`
- `engines/novaact/spikes/negative_assertions.py`
- `engines/novaact/spikes/wikipedia_benchmark.py`
- `engines/novaact/tests/test_workflow_setup.py`

## Audit Trail

- EXTRACTED: 59 (100%)
- INFERRED: 0 (0%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*