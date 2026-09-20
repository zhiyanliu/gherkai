# User Steps Loading

> 26 nodes · cohesion 0.13

## Key Concepts

- **test_user_steps.py** (27 connections) — `engines/novaact/tests/test_user_steps.py`
- **load_user_steps()** (24 connections) — `engines/novaact/gherkai_worker_novaact/user_steps.py`
- **_step_file()** (9 connections) — `engines/novaact/tests/test_user_steps.py`
- **test_excludes_files_under_underscore_dirs()** (4 connections) — `engines/novaact/tests/test_user_steps.py`
- **test_same_basename_in_different_dirs_both_load()** (4 connections) — `engines/novaact/tests/test_user_steps.py`
- **test_excludes_underscore_and_test_prefixed_files()** (3 connections) — `engines/novaact/tests/test_user_steps.py`
- **test_missing_dir_fails_loud()** (3 connections) — `engines/novaact/tests/test_user_steps.py`
- **test_step_file_named_like_stdlib_does_not_shadow()** (3 connections) — `engines/novaact/tests/test_user_steps.py`
- **test_steps_root_not_added_to_sys_path()** (3 connections) — `engines/novaact/tests/test_user_steps.py`
- **test_underscore_dir_still_importable_relatively()** (3 connections) — `engines/novaact/tests/test_user_steps.py`
- **test_underscore_helper_still_importable_relatively()** (3 connections) — `engines/novaact/tests/test_user_steps.py`
- **test_unset_env_is_noop()** (3 connections) — `engines/novaact/tests/test_user_steps.py`
- **test_broken_file_does_not_leave_half_module_in_sys_modules()** (2 connections) — `engines/novaact/tests/test_user_steps.py`
- **test_file_instead_of_dir_fails_loud()** (2 connections) — `engines/novaact/tests/test_user_steps.py`
- **test_import_error_fails_loud_naming_the_file()** (2 connections) — `engines/novaact/tests/test_user_steps.py`
- **test_syntax_error_fails_loud_naming_the_file()** (2 connections) — `engines/novaact/tests/test_user_steps.py`
- **加载 `root` 下的使用方确定性 step 文件，返回实际加载的文件列表（排序后）。 `root` 是 env `GHERKAI_STEPS_DIR`…** (1 connections) — `engines/novaact/gherkai_worker_novaact/user_steps.py`
- **parametrize** (1 connections)
- **使用方 steps 目录加载单测（ADR 0037 决策 4，Nova 侧）。 护住四条不变量（各自对应一个真实会静默出错的场景）： - **排序递归加载 +…** (1 connections) — `engines/novaact/tests/test_user_steps.py`
- **`_pages/` 这类辅助目录同样只是不被自动加载，仍可被 step 文件相对 import（排除它的**用途**）。** (1 connections) — `engines/novaact/tests/test_user_steps.py`
- **`_*` 只是不被**自动加载**，仍可被 step 文件相对 import（这正是它被排除的用途）。** (1 connections) — `engines/novaact/tests/test_user_steps.py`
- **给了目录但不存在就是配置错，不是「没定制」——必须响亮（否则确定性 step 全静默变 AI）。** (1 connections) — `engines/novaact/tests/test_user_steps.py`
- **使用方叫 `json.py` 也不能遮蔽标准库（根不入 sys.path 的实际后果，而非仅断言 sys.path 列表）。** (1 connections) — `engines/novaact/tests/test_user_steps.py`
- **写一个最小 step 文件：顶层 @deterministic 注册（与使用方真实写法逐字一致）。** (1 connections) — `engines/novaact/tests/test_user_steps.py`
- **不同子目录的同名文件都要加载（合成模块名用相对路径、不是 basename，否则后者覆盖前者）。** (1 connections) — `engines/novaact/tests/test_user_steps.py`
- *... and 1 more nodes in this community*

## Relationships

- [User Steps Loading](User_Steps_Loading.md) (8 shared connections)
- [Capabilities Subprocess Tests](Capabilities_Subprocess_Tests.md) (7 shared connections)
- [Nova Act Worker Entry](Nova_Act_Worker_Entry.md) (3 shared connections)
- [Registry Self-Description](Registry_Self-Description.md) (3 shared connections)
- [Deterministic Step Registry](Deterministic_Step_Registry.md) (1 shared connections)
- [AWS Test Fixtures (moto)](AWS_Test_Fixtures_%28moto%29.md) (1 shared connections)

## Source Files

- `engines/novaact/gherkai_worker_novaact/user_steps.py`
- `engines/novaact/tests/test_user_steps.py`

## Audit Trail

- EXTRACTED: 65 (100%)
- INFERRED: 0 (0%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*