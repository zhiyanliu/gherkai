# Deterministic Step Loading

> 51 nodes · cohesion 0.07

## Key Concepts

- **test_user_steps.py** (27 connections) — `engines/novaact/tests/test_user_steps.py`
- **load_user_steps()** (24 connections) — `engines/novaact/gherkai_worker_novaact/user_steps.py`
- **user_steps.py** (11 connections) — `engines/novaact/gherkai_worker_novaact/user_steps.py`
- **_step_file()** (9 connections) — `engines/novaact/tests/test_user_steps.py`
- **UserStepsError** (7 connections) — `engines/novaact/gherkai_worker_novaact/user_steps.py`
- **_clean_env()** (6 connections) — `engines/novaact/tests/test_user_steps.py`
- **list_registry()** (5 connections) — `engines/novaact/gherkai_worker_novaact/deterministic.py`
- **_ensure_ns_package()** (4 connections) — `engines/novaact/gherkai_worker_novaact/user_steps.py`
- **_is_step_file()** (4 connections) — `engines/novaact/gherkai_worker_novaact/user_steps.py`
- **_module_name()** (4 connections) — `engines/novaact/gherkai_worker_novaact/user_steps.py`
- **Path** (4 connections)
- **test_capabilities_subprocess_includes_user_steps()** (4 connections) — `engines/novaact/tests/test_user_steps.py`
- **test_excludes_files_under_underscore_dirs()** (4 connections) — `engines/novaact/tests/test_user_steps.py`
- **test_loaded_count_line_on_stderr_subprocess()** (4 connections) — `engines/novaact/tests/test_user_steps.py`
- **test_loads_recursively_in_sorted_order_and_registers()** (4 connections) — `engines/novaact/tests/test_user_steps.py`
- **test_same_basename_in_different_dirs_both_load()** (4 connections) — `engines/novaact/tests/test_user_steps.py`
- **test_broken_steps_dir_makes_capabilities_exit_nonzero()** (3 connections) — `engines/novaact/tests/test_user_steps.py`
- **test_excludes_underscore_and_test_prefixed_files()** (3 connections) — `engines/novaact/tests/test_user_steps.py`
- **test_missing_dir_fails_loud()** (3 connections) — `engines/novaact/tests/test_user_steps.py`
- **test_no_loaded_line_when_nothing_injected()** (3 connections) — `engines/novaact/tests/test_user_steps.py`
- **test_step_file_named_like_stdlib_does_not_shadow()** (3 connections) — `engines/novaact/tests/test_user_steps.py`
- **test_steps_root_not_added_to_sys_path()** (3 connections) — `engines/novaact/tests/test_user_steps.py`
- **test_underscore_dir_still_importable_relatively()** (3 connections) — `engines/novaact/tests/test_user_steps.py`
- **test_underscore_helper_still_importable_relatively()** (3 connections) — `engines/novaact/tests/test_user_steps.py`
- **test_unset_env_is_noop()** (3 connections) — `engines/novaact/tests/test_user_steps.py`
- *... and 26 more nodes in this community*

## Relationships

- [Nova Act Worker Entry](Nova_Act_Worker_Entry.md) (7 shared connections)
- [Deterministic Step Registry](Deterministic_Step_Registry.md) (4 shared connections)
- [Model Selection ADRs](Model_Selection_ADRs.md) (1 shared connections)
- [Worker Event Sink & Redaction](Worker_Event_Sink_%26_Redaction.md) (1 shared connections)
- [Test Fixtures & Conftest](Test_Fixtures_%26_Conftest.md) (1 shared connections)

## Source Files

- `engines/novaact/gherkai_worker_novaact/deterministic.py`
- `engines/novaact/gherkai_worker_novaact/user_steps.py`
- `engines/novaact/tests/test_user_steps.py`

## Audit Trail

- EXTRACTED: 95 (97%)
- INFERRED: 3 (3%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*