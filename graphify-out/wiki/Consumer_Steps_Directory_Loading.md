# Consumer Steps Directory Loading

> 12 nodes · cohesion 0.20

## Key Concepts

- **user_steps.py** (8 connections) — `engines/novaact/gherkai_worker_novaact/user_steps.py`
- **UserStepsError** (7 connections) — `engines/novaact/gherkai_worker_novaact/user_steps.py`
- **_ensure_ns_package()** (4 connections) — `engines/novaact/gherkai_worker_novaact/user_steps.py`
- **_is_step_file()** (4 connections) — `engines/novaact/gherkai_worker_novaact/user_steps.py`
- **_module_name()** (4 connections) — `engines/novaact/gherkai_worker_novaact/user_steps.py`
- **Path** (4 connections)
- **Exception** (1 connections)
- **加载使用方的确定性 step 目录（ADR 0037 决策 4，Nova 侧实现）。 **约定与解析不在这里**：`--steps-dir` flag >…** (1 connections) — `engines/novaact/gherkai_worker_novaact/user_steps.py`
- **使用方 steps 目录加载失败（目录不存在 / 某文件 import 炸）。 消息自带「哪个文件 +…** (1 connections) — `engines/novaact/gherkai_worker_novaact/user_steps.py`
- **文件路径 → 合成模块名：相对 steps 根的路径，`/` 换 `.`、去 `.py`。 用相对路径（而非仅…** (1 connections) — `engines/novaact/gherkai_worker_novaact/user_steps.py`
- **在 `sys.modules` 里备好一个合成命名空间壳，`__path__` 指向对应真实目录。 `__path__` 让 step 文件里的相对…** (1 connections) — `engines/novaact/gherkai_worker_novaact/user_steps.py`
- **自动加载的筛选（ADR 0037 决策 4）：排除 `_*`（辅助模块，供相对 import）与 `test_*`（使用方自己的测试）。** (1 connections) — `engines/novaact/gherkai_worker_novaact/user_steps.py`

## Relationships

- [User Steps Loading](User_Steps_Loading.md) (8 shared connections)
- [Nova Act Worker](Nova_Act_Worker.md) (2 shared connections)
- [Worker Job Source](Worker_Job_Source.md) (1 shared connections)

## Source Files

- `engines/novaact/gherkai_worker_novaact/user_steps.py`

## Audit Trail

- EXTRACTED: 23 (96%)
- INFERRED: 1 (4%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*