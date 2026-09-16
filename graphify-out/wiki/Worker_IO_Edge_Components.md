# Worker IO Edge Components

> 56 nodes · cohesion 0.05

## Key Concepts

- **test_event_sink.py** (13 connections) — `engines/novaact/tests/test_event_sink.py`
- **ensure_workflow_definition()** (12 connections) — `engines/novaact/gherkai_worker_novaact/lib/workflow_setup.py`
- **_FakeNovaActClient** (12 connections) — `engines/novaact/tests/test_workflow_setup.py`
- **EventSink** (10 connections) — `engines/novaact/gherkai_worker_novaact/lib/event_sink.py`
- **test_workflow_setup.py** (10 connections) — `engines/novaact/tests/test_workflow_setup.py`
- **_patch()** (7 connections) — `engines/novaact/tests/test_workflow_setup.py`
- **workflow_setup.py** (6 connections) — `engines/novaact/gherkai_worker_novaact/lib/workflow_setup.py`
- **negative_assertions.py** (5 connections) — `engines/novaact/spikes/negative_assertions.py`
- **wikipedia_benchmark.py** (5 connections) — `engines/novaact/spikes/wikipedia_benchmark.py`
- **test_concurrent_create_conflict_counts_as_exists()** (5 connections) — `engines/novaact/tests/test_workflow_setup.py`
- **test_other_create_error_propagates()** (5 connections) — `engines/novaact/tests/test_workflow_setup.py`
- **constants.py** (4 connections) — `engines/novaact/gherkai_worker_novaact/lib/constants.py`
- **event_sink.py** (4 connections) — `engines/novaact/gherkai_worker_novaact/lib/event_sink.py`
- **test_create_omits_description_when_absent()** (4 connections) — `engines/novaact/tests/test_workflow_setup.py`
- **test_exists_short_circuits_without_create()** (4 connections) — `engines/novaact/tests/test_workflow_setup.py`
- **test_missing_definition_is_created()** (4 connections) — `engines/novaact/tests/test_workflow_setup.py`
- **._ddb()** (3 connections) — `engines/novaact/gherkai_worker_novaact/lib/event_sink.py`
- **.emit()** (3 connections) — `engines/novaact/gherkai_worker_novaact/lib/event_sink.py`
- **exceptions** (3 connections) — `engines/novaact/tests/test_workflow_setup.py`
- **Exception** (3 connections)
- **.__init__()** (2 connections) — `engines/novaact/gherkai_worker_novaact/lib/event_sink.py`
- **lib/__init__.py** (2 connections) — `engines/novaact/gherkai_worker_novaact/lib/__init__.py`
- **main()** (2 connections) — `engines/novaact/spikes/negative_assertions.py`
- **run()** (2 connections) — `engines/novaact/spikes/wikipedia_benchmark.py`
- **test_ddb_mode_missing_run_or_scope_id_fails_loud()** (2 connections) — `engines/novaact/tests/test_event_sink.py`
- *... and 31 more nodes in this community*

## Relationships

- [Nova Act Worker Package](Nova_Act_Worker_Package.md) (7 shared connections)
- [Backend CDK Stack](Backend_CDK_Stack.md) (1 shared connections)
- [Cloud Target & Worker Resolution](Cloud_Target_%26_Worker_Resolution.md) (1 shared connections)

## Source Files

- `engines/novaact/gherkai_worker_novaact/lib/__init__.py`
- `engines/novaact/gherkai_worker_novaact/lib/constants.py`
- `engines/novaact/gherkai_worker_novaact/lib/event_sink.py`
- `engines/novaact/gherkai_worker_novaact/lib/workflow_setup.py`
- `engines/novaact/spikes/negative_assertions.py`
- `engines/novaact/spikes/wikipedia_benchmark.py`
- `engines/novaact/tests/test_event_sink.py`
- `engines/novaact/tests/test_workflow_setup.py`

## Audit Trail

- EXTRACTED: 86 (98%)
- INFERRED: 2 (2%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*