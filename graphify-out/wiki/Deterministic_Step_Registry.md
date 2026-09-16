# Deterministic Step Registry

> 34 nodes · cohesion 0.09

## Key Concepts

- **deterministic.py** (17 connections) — `engines/novaact/gherkai_worker_novaact/deterministic.py`
- **test_deterministic.py** (14 connections) — `engines/novaact/tests/test_deterministic.py`
- **deterministic()** (13 connections) — `engines/novaact/gherkai_worker_novaact/deterministic.py`
- **match()** (10 connections) — `engines/novaact/gherkai_worker_novaact/deterministic.py`
- **_hits()** (5 connections) — `engines/novaact/gherkai_worker_novaact/deterministic.py`
- **list_registry()** (5 connections) — `engines/novaact/gherkai_worker_novaact/deterministic.py`
- **match_batch()** (5 connections) — `engines/novaact/gherkai_worker_novaact/deterministic.py`
- **DeterministicConflict** (4 connections) — `engines/novaact/gherkai_worker_novaact/deterministic.py`
- **test_match_batch_hit_miss_conflict()** (4 connections) — `engines/novaact/tests/test_deterministic.py`
- **_isolate()** (3 connections) — `engines/novaact/tests/test_deterministic.py`
- **test_handler_assertion_propagates()** (3 connections) — `engines/novaact/tests/test_deterministic.py`
- **test_list_registry_reflects_registrations()** (3 connections) — `engines/novaact/tests/test_deterministic.py`
- **test_miss_returns_none()** (3 connections) — `engines/novaact/tests/test_deterministic.py`
- **test_missing_metadata_fails_loud()** (3 connections) — `engines/novaact/tests/test_deterministic.py`
- **test_multiple_hits_raises_conflict()** (3 connections) — `engines/novaact/tests/test_deterministic.py`
- **test_no_named_groups_empty_dict()** (3 connections) — `engines/novaact/tests/test_deterministic.py`
- **test_register_and_match_with_named_groups()** (3 connections) — `engines/novaact/tests/test_deterministic.py`
- **clear()** (2 connections) — `engines/novaact/gherkai_worker_novaact/deterministic.py`
- **_Entry** (2 connections) — `engines/novaact/gherkai_worker_novaact/deterministic.py`
- **test_worker_dump_mode_real_subprocess()** (2 connections) — `engines/novaact/tests/test_deterministic.py`
- **test_worker_match_steps_mode_real_subprocess()** (2 connections) — `engines/novaact/tests/test_deterministic.py`
- **Exception** (1 connections)
- **确定性 step 注册表（ADR 0022）——Nova 引擎。 测试开发用 `@deterministic(pattern)` 把「正则模式 →…** (1 connections) — `engines/novaact/gherkai_worker_novaact/deterministic.py`
- **批量 match 查询（ADR 0036 决策 4）：plan 命中标注用——对每条 step 文本回答「命中哪条 / 冲突 / 未命中」。 与…** (1 connections) — `engines/novaact/gherkai_worker_novaact/deterministic.py`
- **装饰器：把 handler 按正则 pattern 登记进注册表。 description/example 必填（ADR…** (1 connections) — `engines/novaact/gherkai_worker_novaact/deterministic.py`
- *... and 9 more nodes in this community*

## Relationships

- [Nova Act Worker Package](Nova_Act_Worker_Package.md) (4 shared connections)
- [User Steps Loading](User_Steps_Loading.md) (4 shared connections)
- [Step Execution & Error Classification](Step_Execution_%26_Error_Classification.md) (3 shared connections)
- [Built-in Deterministic Steps](Built-in_Deterministic_Steps.md) (2 shared connections)
- [Engine & Protocol ADRs](Engine_%26_Protocol_ADRs.md) (1 shared connections)
- [Backend CDK Stack](Backend_CDK_Stack.md) (1 shared connections)
- [AWS Test Fixtures](AWS_Test_Fixtures.md) (1 shared connections)

## Source Files

- `engines/novaact/gherkai_worker_novaact/deterministic.py`
- `engines/novaact/tests/test_deterministic.py`

## Audit Trail

- EXTRACTED: 66 (96%)
- INFERRED: 3 (4%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*