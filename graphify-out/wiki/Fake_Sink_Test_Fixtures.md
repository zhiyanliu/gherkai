# Fake Sink Test Fixtures

> 11 nodes · cohesion 0.18

## Key Concepts

- **_FakeSink** (9 connections) — `engines/novaact/tests/test_run_step.py`
- **captured()** (4 connections) — `engines/novaact/tests/test_run_step.py`
- **.clear()** (1 connections) — `engines/novaact/tests/test_run_step.py`
- **.emit()** (1 connections) — `engines/novaact/tests/test_run_step.py`
- **.__getitem__()** (1 connections) — `engines/novaact/tests/test_run_step.py`
- **.__init__()** (1 connections) — `engines/novaact/tests/test_run_step.py`
- **.__iter__()** (1 connections) — `engines/novaact/tests/test_run_step.py`
- **.__len__()** (1 connections) — `engines/novaact/tests/test_run_step.py`
- **fixture** (1 connections)
- **假 EventSink（ADR 0024 I/O 边缘可注入接口，参数注入使测试可注 fake）：emit 收集事件、且 list-like…** (1 connections) — `engines/novaact/tests/test_run_step.py`
- **假 sink：收集 _run_step/_run_scenario 经 sink.emit 吐的事件供断言（作 sink 参数注入，对称 Midscene）。** (1 connections) — `engines/novaact/tests/test_run_step.py`

## Relationships

- [Step Dispatch & Error Mapping](Step_Dispatch_%26_Error_Mapping.md) (2 shared connections)

## Source Files

- `engines/novaact/tests/test_run_step.py`

## Audit Trail

- EXTRACTED: 12 (100%)
- INFERRED: 0 (0%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*