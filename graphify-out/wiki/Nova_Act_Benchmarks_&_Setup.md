# Nova Act Benchmarks & Setup

> 54 nodes · cohesion 0.06

## Key Concepts

- **ensure_workflow_definition()** (12 connections) — `engines/novaact/gherkai_worker_novaact/lib/workflow_setup.py`
- **_FakeNovaActClient** (12 connections) — `engines/novaact/tests/test_workflow_setup.py`
- **test_capabilities.py** (11 connections) — `engines/novaact/tests/test_capabilities.py`
- **_clean_env()** (10 connections) — `engines/novaact/tests/test_capabilities.py`
- **test_workflow_setup.py** (10 connections) — `engines/novaact/tests/test_workflow_setup.py`
- **_patch()** (7 connections) — `engines/novaact/tests/test_workflow_setup.py`
- **workflow_setup.py** (6 connections) — `engines/novaact/gherkai_worker_novaact/lib/workflow_setup.py`
- **constants.py** (5 connections) — `engines/novaact/gherkai_worker_novaact/lib/constants.py`
- **negative_assertions.py** (5 connections) — `engines/novaact/spikes/negative_assertions.py`
- **wikipedia_benchmark.py** (5 connections) — `engines/novaact/spikes/wikipedia_benchmark.py`
- **test_concurrent_create_conflict_counts_as_exists()** (5 connections) — `engines/novaact/tests/test_workflow_setup.py`
- **test_other_create_error_propagates()** (5 connections) — `engines/novaact/tests/test_workflow_setup.py`
- **test_create_omits_description_when_absent()** (4 connections) — `engines/novaact/tests/test_workflow_setup.py`
- **test_exists_short_circuits_without_create()** (4 connections) — `engines/novaact/tests/test_workflow_setup.py`
- **test_missing_definition_is_created()** (4 connections) — `engines/novaact/tests/test_workflow_setup.py`
- **test_broken_steps_dir_makes_capabilities_exit_nonzero()** (3 connections) — `engines/novaact/tests/test_capabilities.py`
- **test_capabilities_shape_and_min_grace_from_injected_act_timeout()** (3 connections) — `engines/novaact/tests/test_capabilities.py`
- **test_default_min_grace_covers_act_timeout_default()** (3 connections) — `engines/novaact/tests/test_capabilities.py`
- **test_does_not_read_stdin()** (3 connections) — `engines/novaact/tests/test_capabilities.py`
- **test_list_deterministic_flag_no_longer_recognized()** (3 connections) — `engines/novaact/tests/test_capabilities.py`
- **test_min_grace_tracks_both_env_knobs()** (3 connections) — `engines/novaact/tests/test_capabilities.py`
- **test_model_id_defaults_to_pinned_ga_version()** (3 connections) — `engines/novaact/tests/test_capabilities.py`
- **test_model_id_follows_env_override()** (3 connections) — `engines/novaact/tests/test_capabilities.py`
- **exceptions** (3 connections) — `engines/novaact/tests/test_workflow_setup.py`
- **Exception** (3 connections)
- *... and 29 more nodes in this community*

## Relationships

- [Nova Act Worker Entry](Nova_Act_Worker_Entry.md) (4 shared connections)

## Source Files

- `engines/novaact/gherkai_worker_novaact/lib/__init__.py`
- `engines/novaact/gherkai_worker_novaact/lib/constants.py`
- `engines/novaact/gherkai_worker_novaact/lib/workflow_setup.py`
- `engines/novaact/spikes/negative_assertions.py`
- `engines/novaact/spikes/wikipedia_benchmark.py`
- `engines/novaact/tests/test_capabilities.py`
- `engines/novaact/tests/test_workflow_setup.py`

## Audit Trail

- EXTRACTED: 87 (100%)
- INFERRED: 0 (0%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*