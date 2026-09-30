# Deterministic Registry (Python)

> 12 nodes · cohesion 0.20

## Key Concepts

- **deterministic.py** (14 connections) — `engines/novaact/gherkai_worker_novaact/deterministic.py`
- **_hits()** (5 connections) — `engines/novaact/gherkai_worker_novaact/deterministic.py`
- **match_batch()** (5 connections) — `engines/novaact/gherkai_worker_novaact/deterministic.py`
- **DeterministicConflict** (4 connections) — `engines/novaact/gherkai_worker_novaact/deterministic.py`
- **_isolate()** (3 connections) — `engines/novaact/tests/test_deterministic.py`
- **clear()** (2 connections) — `engines/novaact/gherkai_worker_novaact/deterministic.py`
- **_Entry** (2 connections) — `engines/novaact/gherkai_worker_novaact/deterministic.py`
- **Exception** (1 connections)
- **确定性 step 注册表（ADR 0022）——Nova 引擎。 测试开发用 `@deterministic(pattern)` 把「正则模式 →…** (1 connections) — `engines/novaact/gherkai_worker_novaact/deterministic.py`
- **批量 match 查询（ADR 0036 决策 4）：plan 命中标注用——对每条 step 文本回答「命中哪条 / 冲突 / 未命中」。 与…** (1 connections) — `engines/novaact/gherkai_worker_novaact/deterministic.py`
- **一个 step 文本命中多条确定性模式（ADR 0022：最多命中一条，多条是配置错误）。 冲突清单只经 message 传（派发侧把异常文本并入…** (1 connections) — `engines/novaact/gherkai_worker_novaact/deterministic.py`
- **扫注册表收**全部**命中——match（实际运行派发）与 match_batch（用例预检）唯一的扫描实现面。…** (1 connections) — `engines/novaact/gherkai_worker_novaact/deterministic.py`

## Relationships

- [Deterministic Step Registry](Deterministic_Step_Registry.md) (7 shared connections)
- [Built-in Deterministic Steps](Built-in_Deterministic_Steps.md) (1 shared connections)
- [Nova Act Worker Runtime](Nova_Act_Worker_Runtime.md) (1 shared connections)
- [Step and Scenario Execution](Step_and_Scenario_Execution.md) (1 shared connections)
- [User Steps Directory Loading](User_Steps_Directory_Loading.md) (1 shared connections)
- [Registry Self-Description](Registry_Self-Description.md) (1 shared connections)
- [Nova Worker Process Entry](Nova_Worker_Process_Entry.md) (1 shared connections)
- [CLI Test Fixtures](CLI_Test_Fixtures.md) (1 shared connections)

## Source Files

- `engines/novaact/gherkai_worker_novaact/deterministic.py`
- `engines/novaact/tests/test_deterministic.py`

## Audit Trail

- EXTRACTED: 27 (100%)
- INFERRED: 0 (0%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*