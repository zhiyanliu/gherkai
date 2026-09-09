# Deterministic Step Registry

> 22 nodes · cohesion 0.14

## Key Concepts

- **test_deterministic.py** (14 connections) — `engines/novaact/tests/test_deterministic.py`
- **deterministic()** (12 connections) — `engines/novaact/gherkai_worker_novaact/deterministic.py`
- **match()** (10 connections) — `engines/novaact/gherkai_worker_novaact/deterministic.py`
- **list_registry()** (5 connections) — `engines/novaact/gherkai_worker_novaact/deterministic.py`
- **test_match_batch_hit_miss_conflict()** (4 connections) — `engines/novaact/tests/test_deterministic.py`
- **test_handler_assertion_propagates()** (3 connections) — `engines/novaact/tests/test_deterministic.py`
- **test_list_registry_reflects_registrations()** (3 connections) — `engines/novaact/tests/test_deterministic.py`
- **test_miss_returns_none()** (3 connections) — `engines/novaact/tests/test_deterministic.py`
- **test_missing_metadata_fails_loud()** (3 connections) — `engines/novaact/tests/test_deterministic.py`
- **test_multiple_hits_raises_conflict()** (3 connections) — `engines/novaact/tests/test_deterministic.py`
- **test_no_named_groups_empty_dict()** (3 connections) — `engines/novaact/tests/test_deterministic.py`
- **test_register_and_match_with_named_groups()** (3 connections) — `engines/novaact/tests/test_deterministic.py`
- **test_worker_dump_mode_real_subprocess()** (2 connections) — `engines/novaact/tests/test_deterministic.py`
- **test_worker_match_steps_mode_real_subprocess()** (2 connections) — `engines/novaact/tests/test_deterministic.py`
- **装饰器：把 handler 按正则 pattern 登记进注册表。 description/example 必填（ADR…** (1 connections) — `engines/novaact/gherkai_worker_novaact/deterministic.py`
- **注册表自述（ADR 0036）：worker --list-deterministic 时 dump 成 JSON 给 CLI 转述。** (1 connections) — `engines/novaact/gherkai_worker_novaact/deterministic.py`
- **在注册表里找命中 text 的唯一 handler。 返回 (handler, groups_dict) 或 None（未命中走 AI）。命中多条 →…** (1 connections) — `engines/novaact/gherkai_worker_novaact/deterministic.py`
- **确定性注册表单测（ADR 0022）——纯单元，不连 AWS、不起浏览器。 跑（从 repo 根）：uv run pytest -q…** (1 connections) — `engines/novaact/tests/test_deterministic.py`
- **--match-steps 自述模式真子进程：stdin JSON 数组 → 逐条命中结果（真锚点命中面与派发一致）。** (1 connections) — `engines/novaact/tests/test_deterministic.py`
- **description/example 必填（ADR 0036：注册即暴露，缺元数据 = 能力不可发现，fail-loud）。** (1 connections) — `engines/novaact/tests/test_deterministic.py`
- **--list-deterministic 自述模式（ADR 0036）真子进程：不读 stdin、输出 JSON、含脚手架真锚点。** (1 connections) — `engines/novaact/tests/test_deterministic.py`
- **match_batch（ADR 0036 决策 4）：命中/未命中/冲突结构化返回（冲突不抛——plan 是预检不是执行）。** (1 connections) — `engines/novaact/tests/test_deterministic.py`

## Relationships

- [Nova Deterministic Registry](Nova_Deterministic_Registry.md) (8 shared connections)
- [Nova Act Worker](Nova_Act_Worker.md) (2 shared connections)
- [Deterministic Step Scaffolding](Deterministic_Step_Scaffolding.md) (1 shared connections)
- [Env Config & Error Classification](Env_Config_%26_Error_Classification.md) (1 shared connections)
- [User Steps Loading](User_Steps_Loading.md) (1 shared connections)
- [Step Dispatch Execution](Step_Dispatch_Execution.md) (1 shared connections)

## Source Files

- `engines/novaact/gherkai_worker_novaact/deterministic.py`
- `engines/novaact/tests/test_deterministic.py`

## Audit Trail

- EXTRACTED: 45 (98%)
- INFERRED: 1 (2%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*