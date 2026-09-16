# User Steps Loading

> 40 nodes · cohesion 0.08

## Key Concepts

- **test_user_steps.py** (27 connections) — `engines/novaact/tests/test_user_steps.py`
- **load_user_steps()** (24 connections) — `engines/novaact/gherkai_worker_novaact/user_steps.py`
- **_step_file()** (9 connections) — `engines/novaact/tests/test_user_steps.py`
- **UserStepsError** (7 connections) — `engines/novaact/gherkai_worker_novaact/user_steps.py`
- **_clean_env()** (6 connections) — `engines/novaact/tests/test_user_steps.py`
- **test_excludes_files_under_underscore_dirs()** (4 connections) — `engines/novaact/tests/test_user_steps.py`
- **test_list_deterministic_subprocess_includes_user_steps()** (4 connections) — `engines/novaact/tests/test_user_steps.py`
- **test_loaded_count_line_on_stderr_subprocess()** (4 connections) — `engines/novaact/tests/test_user_steps.py`
- **test_loads_recursively_in_sorted_order_and_registers()** (4 connections) — `engines/novaact/tests/test_user_steps.py`
- **test_same_basename_in_different_dirs_both_load()** (4 connections) — `engines/novaact/tests/test_user_steps.py`
- **test_broken_steps_dir_makes_list_deterministic_exit_nonzero()** (3 connections) — `engines/novaact/tests/test_user_steps.py`
- **test_excludes_underscore_and_test_prefixed_files()** (3 connections) — `engines/novaact/tests/test_user_steps.py`
- **test_missing_dir_fails_loud()** (3 connections) — `engines/novaact/tests/test_user_steps.py`
- **test_no_loaded_line_when_nothing_injected()** (3 connections) — `engines/novaact/tests/test_user_steps.py`
- **test_step_file_named_like_stdlib_does_not_shadow()** (3 connections) — `engines/novaact/tests/test_user_steps.py`
- **test_steps_root_not_added_to_sys_path()** (3 connections) — `engines/novaact/tests/test_user_steps.py`
- **test_underscore_dir_still_importable_relatively()** (3 connections) — `engines/novaact/tests/test_user_steps.py`
- **test_underscore_helper_still_importable_relatively()** (3 connections) — `engines/novaact/tests/test_user_steps.py`
- **test_unset_env_is_noop()** (3 connections) — `engines/novaact/tests/test_user_steps.py`
- **test_broken_file_does_not_leave_half_module_in_sys_modules()** (2 connections) — `engines/novaact/tests/test_user_steps.py`
- **test_file_instead_of_dir_fails_loud()** (2 connections) — `engines/novaact/tests/test_user_steps.py`
- **test_import_error_fails_loud_naming_the_file()** (2 connections) — `engines/novaact/tests/test_user_steps.py`
- **test_syntax_error_fails_loud_naming_the_file()** (2 connections) — `engines/novaact/tests/test_user_steps.py`
- **Exception** (1 connections)
- **使用方 steps 目录加载失败（目录不存在 / 某文件 import 炸）。 消息自带「哪个文件 +…** (1 connections) — `engines/novaact/gherkai_worker_novaact/user_steps.py`
- *... and 15 more nodes in this community*

## Relationships

- [User Steps Loading](User_Steps_Loading.md) (7 shared connections)
- [Nova Act Worker Package](Nova_Act_Worker_Package.md) (5 shared connections)
- [Deterministic Step Registry](Deterministic_Step_Registry.md) (2 shared connections)
- [AWS Test Fixtures](AWS_Test_Fixtures.md) (1 shared connections)

## Source Files

- `engines/novaact/gherkai_worker_novaact/user_steps.py`
- `engines/novaact/tests/test_user_steps.py`

## Audit Trail

- EXTRACTED: 79 (99%)
- INFERRED: 1 (1%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*