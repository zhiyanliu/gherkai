# Capabilities Subprocess Tests

> 10 nodes · cohesion 0.20

## Key Concepts

- **_clean_env()** (6 connections) — `engines/novaact/tests/test_user_steps.py`
- **test_capabilities_subprocess_includes_user_steps()** (4 connections) — `engines/novaact/tests/test_user_steps.py`
- **test_loaded_count_line_on_stderr_subprocess()** (4 connections) — `engines/novaact/tests/test_user_steps.py`
- **test_broken_steps_dir_makes_capabilities_exit_nonzero()** (3 connections) — `engines/novaact/tests/test_user_steps.py`
- **test_no_loaded_line_when_nothing_injected()** (3 connections) — `engines/novaact/tests/test_user_steps.py`
- **真子进程 + 真 env：`-m gherkai_worker_novaact --capabilities` 的 `deterministic_steps`…** (1 connections) — `engines/novaact/tests/test_user_steps.py`
- **fail-loud 到进程边界：坏 step 文件 → 自述入口也非 0 退出、stderr 指名文件（不静默给出残缺清单）。** (1 connections) — `engines/novaact/tests/test_user_steps.py`
- **加载成功也留一行 stderr（文件数 + 目录）：使用方据它分清「目录没被读到」与「pattern 没命中」。** (1 connections) — `engines/novaact/tests/test_user_steps.py`
- **未注入目录表示使用方没定制，正常路径不打这行（诊断行不许变成人人都看见的噪声）。** (1 connections) — `engines/novaact/tests/test_user_steps.py`
- **子进程 env：保留 PATH/PYTHONPATH 等运行必需项，剥掉可能干扰的 GHERKAI_* / AWS 落点。** (1 connections) — `engines/novaact/tests/test_user_steps.py`

## Relationships

- [User Steps Loading](User_Steps_Loading.md) (7 shared connections)

## Source Files

- `engines/novaact/tests/test_user_steps.py`

## Audit Trail

- EXTRACTED: 16 (100%)
- INFERRED: 0 (0%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*