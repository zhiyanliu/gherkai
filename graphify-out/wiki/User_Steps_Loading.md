# User Steps Loading

> 29 nodes · cohesion 0.12

## Key Concepts

- **test_user_steps.py** (23 connections) — `engines/novaact/tests/test_user_steps.py`
- **load_user_steps()** (22 connections) — `engines/novaact/gherkai_worker_novaact/user_steps.py`
- **_step_file()** (7 connections) — `engines/novaact/tests/test_user_steps.py`
- **_clean_env()** (4 connections) — `engines/novaact/tests/test_user_steps.py`
- **test_list_deterministic_subprocess_includes_user_steps()** (4 connections) — `engines/novaact/tests/test_user_steps.py`
- **test_loads_recursively_in_sorted_order_and_registers()** (4 connections) — `engines/novaact/tests/test_user_steps.py`
- **test_same_basename_in_different_dirs_both_load()** (4 connections) — `engines/novaact/tests/test_user_steps.py`
- **test_broken_steps_dir_makes_list_deterministic_exit_nonzero()** (3 connections) — `engines/novaact/tests/test_user_steps.py`
- **test_excludes_underscore_and_test_prefixed_files()** (3 connections) — `engines/novaact/tests/test_user_steps.py`
- **test_missing_dir_fails_loud()** (3 connections) — `engines/novaact/tests/test_user_steps.py`
- **test_step_file_named_like_stdlib_does_not_shadow()** (3 connections) — `engines/novaact/tests/test_user_steps.py`
- **test_steps_root_not_added_to_sys_path()** (3 connections) — `engines/novaact/tests/test_user_steps.py`
- **test_underscore_helper_still_importable_relatively()** (3 connections) — `engines/novaact/tests/test_user_steps.py`
- **test_unset_env_is_noop()** (3 connections) — `engines/novaact/tests/test_user_steps.py`
- **test_broken_file_does_not_leave_half_module_in_sys_modules()** (2 connections) — `engines/novaact/tests/test_user_steps.py`
- **test_file_instead_of_dir_fails_loud()** (2 connections) — `engines/novaact/tests/test_user_steps.py`
- **test_import_error_fails_loud_naming_the_file()** (2 connections) — `engines/novaact/tests/test_user_steps.py`
- **test_syntax_error_fails_loud_naming_the_file()** (2 connections) — `engines/novaact/tests/test_user_steps.py`
- **加载 `root` 下的使用方确定性 step 文件，返回实际加载的文件列表（排序后）。 `root` = env `GHERKAI_STEPS_DIR`…** (1 connections) — `engines/novaact/gherkai_worker_novaact/user_steps.py`
- **parametrize** (1 connections)
- **使用方 steps 目录加载单测（ADR 0037 决策 4，Nova 侧）。 护住四条不变量（各自对应一个真实会静默出错的场景）： - **排序递归加载 +…** (1 connections) — `engines/novaact/tests/test_user_steps.py`
- **给了目录但不存在 = 配置错，不是「没定制」——必须响亮（否则确定性 step 全静默变 AI）。** (1 connections) — `engines/novaact/tests/test_user_steps.py`
- **使用方叫 `json.py` 也不能遮蔽标准库（根不入 sys.path 的实际后果，而非仅断言 sys.path 列表）。** (1 connections) — `engines/novaact/tests/test_user_steps.py`
- **真子进程 + 真 env：`-m gherkai_worker_novaact --list-deterministic` 报的表含使用方 step。…** (1 connections) — `engines/novaact/tests/test_user_steps.py`
- **fail-loud 到进程边界：坏 step 文件 → 自述入口也非 0 退出、stderr 指名文件（不静默给出残缺清单）。** (1 connections) — `engines/novaact/tests/test_user_steps.py`
- *... and 4 more nodes in this community*

## Relationships

- [Consumer Steps Directory Loading](Consumer_Steps_Directory_Loading.md) (8 shared connections)
- [Nova Act Worker](Nova_Act_Worker.md) (3 shared connections)
- [Nova Deterministic Registry](Nova_Deterministic_Registry.md) (1 shared connections)
- [Module Registry Isolation](Module_Registry_Isolation.md) (1 shared connections)
- [Deterministic Step Registry](Deterministic_Step_Registry.md) (1 shared connections)

## Source Files

- `engines/novaact/gherkai_worker_novaact/user_steps.py`
- `engines/novaact/tests/test_user_steps.py`

## Audit Trail

- EXTRACTED: 61 (100%)
- INFERRED: 0 (0%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*