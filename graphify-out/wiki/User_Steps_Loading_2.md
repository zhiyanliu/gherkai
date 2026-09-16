# User Steps Loading

> 15 nodes · cohesion 0.16

## Key Concepts

- **user_steps.py** (11 connections) — `engines/novaact/gherkai_worker_novaact/user_steps.py`
- **src/worker/deterministic.mts — 确定性注册表** (4 connections) — `engines/midscene/DEVELOPMENT.md`
- **src/worker/user-steps.mts — 使用方 steps 加载** (4 connections) — `engines/midscene/DEVELOPMENT.md`
- **_ensure_ns_package()** (4 connections) — `engines/novaact/gherkai_worker_novaact/user_steps.py`
- **_is_step_file()** (4 connections) — `engines/novaact/gherkai_worker_novaact/user_steps.py`
- **_module_name()** (4 connections) — `engines/novaact/gherkai_worker_novaact/user_steps.py`
- **Path** (4 connections)
- **steps 加载 fail-loud 不静默降级** (3 connections) — `engines/novaact/README.md`
- **compose.query_deterministic / match_deterministic** (3 connections) — `runtime/DEVELOPMENT.md`
- **src/index.mts — 包公开 API** (2 connections) — `engines/midscene/DEVELOPMENT.md`
- **src/worker/deterministic.steps.mts — 内建脚手架 step** (1 connections) — `engines/midscene/DEVELOPMENT.md`
- **加载使用方的确定性 step 目录（ADR 0037 决策 4，Nova 侧实现）。 **约定与解析不在这里**：`--steps-dir` flag >…** (1 connections) — `engines/novaact/gherkai_worker_novaact/user_steps.py`
- **文件路径 → 合成模块名：相对 steps 根的路径，`/` 换 `.`、去 `.py`。 用相对路径（而非仅…** (1 connections) — `engines/novaact/gherkai_worker_novaact/user_steps.py`
- **在 `sys.modules` 里备好一个合成命名空间壳，`__path__` 指向对应真实目录。 `__path__` 让 step 文件里的相对…** (1 connections) — `engines/novaact/gherkai_worker_novaact/user_steps.py`
- **自动加载的筛选（ADR 0037 决策 4）：排除 `_` 开头的**文件或目录**（辅助模块，供其它 step 文件 import） 与 `test_*`…** (1 connections) — `engines/novaact/gherkai_worker_novaact/user_steps.py`

## Relationships

- [User Steps Loading](User_Steps_Loading.md) (7 shared connections)
- [Engine & Protocol ADRs](Engine_%26_Protocol_ADRs.md) (2 shared connections)
- [Deterministic Step Registry](Deterministic_Step_Registry.md) (2 shared connections)
- [Midscene Worker Entry & SigV4](Midscene_Worker_Entry_%26_SigV4.md) (1 shared connections)
- [Nova Act Worker Package](Nova_Act_Worker_Package.md) (1 shared connections)
- [Compose Root & ADR Links](Compose_Root_%26_ADR_Links.md) (1 shared connections)

## Source Files

- `engines/midscene/DEVELOPMENT.md`
- `engines/novaact/README.md`
- `engines/novaact/gherkai_worker_novaact/user_steps.py`
- `runtime/DEVELOPMENT.md`

## Audit Trail

- EXTRACTED: 27 (87%)
- INFERRED: 4 (13%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*