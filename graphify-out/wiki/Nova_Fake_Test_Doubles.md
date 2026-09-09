# Nova Fake Test Doubles

> 13 nodes · cohesion 0.17

## Key Concepts

- **_FakeResult** (7 connections) — `engines/novaact/tests/test_run_step.py`
- **_NavErrorNova** (7 connections) — `engines/novaact/tests/test_run_step.py`
- **_Meta** (3 connections) — `engines/novaact/tests/test_run_step.py`
- **.act()** (2 connections) — `engines/novaact/tests/test_run_step.py`
- **.act_get()** (2 connections) — `engines/novaact/tests/test_run_step.py`
- **.__init__()** (2 connections) — `engines/novaact/tests/test_run_step.py`
- **.act()** (2 connections) — `engines/novaact/tests/test_run_step.py`
- **.act_get()** (2 connections) — `engines/novaact/tests/test_run_step.py`
- **.__init__()** (1 connections) — `engines/novaact/tests/test_run_step.py`
- **.go_to_url()** (1 connections) — `engines/novaact/tests/test_run_step.py`
- **.__init__()** (1 connections) — `engines/novaact/tests/test_run_step.py`
- **模拟 nova.act_get 返回：带 matches_schema/parsed_response（投票布尔依据）+…** (1 connections) — `engines/novaact/tests/test_run_step.py`
- **go_to_url 抛异常（模拟导航 SSL 失败 → step error）；act/act_get 记调用（验证短路后不再被调）。** (1 connections) — `engines/novaact/tests/test_run_step.py`

## Relationships

- [Step Dispatch Execution](Step_Dispatch_Execution.md) (6 shared connections)

## Source Files

- `engines/novaact/tests/test_run_step.py`

## Audit Trail

- EXTRACTED: 19 (100%)
- INFERRED: 0 (0%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*