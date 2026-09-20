# Deterministic Step Registry

> 19 nodes · cohesion 0.16

## Key Concepts

- **test_deterministic.py** (14 connections) — `engines/novaact/tests/test_deterministic.py`
- **deterministic()** (13 connections) — `engines/novaact/gherkai_worker_novaact/deterministic.py`
- **match()** (10 connections) — `engines/novaact/gherkai_worker_novaact/deterministic.py`
- **test_match_batch_hit_miss_conflict()** (4 connections) — `engines/novaact/tests/test_deterministic.py`
- **test_handler_assertion_propagates()** (3 connections) — `engines/novaact/tests/test_deterministic.py`
- **test_miss_returns_none()** (3 connections) — `engines/novaact/tests/test_deterministic.py`
- **test_missing_metadata_fails_loud()** (3 connections) — `engines/novaact/tests/test_deterministic.py`
- **test_multiple_hits_raises_conflict()** (3 connections) — `engines/novaact/tests/test_deterministic.py`
- **test_no_named_groups_empty_dict()** (3 connections) — `engines/novaact/tests/test_deterministic.py`
- **test_register_and_match_with_named_groups()** (3 connections) — `engines/novaact/tests/test_deterministic.py`
- **test_registry_dump_via_capabilities_real_subprocess()** (2 connections) — `engines/novaact/tests/test_deterministic.py`
- **test_worker_match_steps_mode_real_subprocess()** (2 connections) — `engines/novaact/tests/test_deterministic.py`
- **装饰器：把 handler 按正则 pattern 登记进注册表。 description/example 必填（ADR…** (1 connections) — `engines/novaact/gherkai_worker_novaact/deterministic.py`
- **在注册表里找命中 text 的唯一 handler。 返回 (handler, groups_dict) 或 None（未命中走 AI）。命中多条 →…** (1 connections) — `engines/novaact/gherkai_worker_novaact/deterministic.py`
- **确定性注册表单测（ADR 0022）——纯单元，不连 AWS、不起浏览器。 运行（从 repo 根）：uv run pytest -q…** (1 connections) — `engines/novaact/tests/test_deterministic.py`
- **--match-steps 自述模式真子进程：stdin JSON 数组 → 逐条命中结果（真 step 命中面与派发一致）。** (1 connections) — `engines/novaact/tests/test_deterministic.py`
- **description/example 必填（ADR 0036：注册即暴露，缺元数据意味着能力不可发现，fail-loud）。** (1 connections) — `engines/novaact/tests/test_deterministic.py`
- **注册表清单经自述入口出去（ADR 0036「2.」/「5.」）真子进程：`--capabilities` 的 `deterministic_steps`…** (1 connections) — `engines/novaact/tests/test_deterministic.py`
- **match_batch（ADR 0036 决策 4）：命中/未命中/冲突结构化返回（冲突不抛——plan 是用例预检、不是执行）。** (1 connections) — `engines/novaact/tests/test_deterministic.py`

## Relationships

- [Deterministic Step Registry](Deterministic_Step_Registry.md) (7 shared connections)
- [Registry Self-Description](Registry_Self-Description.md) (2 shared connections)
- [Step Dispatch & Voting](Step_Dispatch_%26_Voting.md) (2 shared connections)
- [Builtin Deterministic Steps](Builtin_Deterministic_Steps.md) (1 shared connections)
- [Backend CDK Stack](Backend_CDK_Stack.md) (1 shared connections)
- [Nova Act Worker Entry](Nova_Act_Worker_Entry.md) (1 shared connections)

## Source Files

- `engines/novaact/gherkai_worker_novaact/deterministic.py`
- `engines/novaact/tests/test_deterministic.py`

## Audit Trail

- EXTRACTED: 41 (98%)
- INFERRED: 1 (2%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*