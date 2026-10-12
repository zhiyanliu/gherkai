# Fake Event Sink

> 9 nodes · cohesion 0.22

## Key Concepts

- **_FakeSink** (8 connections) — `engines/novaact/tests/test_interrupt_model.py`
- **captured()** (4 connections) — `engines/novaact/tests/test_interrupt_model.py`
- **.emit()** (1 connections) — `engines/novaact/tests/test_interrupt_model.py`
- **.__getitem__()** (1 connections) — `engines/novaact/tests/test_interrupt_model.py`
- **.__init__()** (1 connections) — `engines/novaact/tests/test_interrupt_model.py`
- **.__iter__()** (1 connections) — `engines/novaact/tests/test_interrupt_model.py`
- **.__len__()** (1 connections) — `engines/novaact/tests/test_interrupt_model.py`
- **假 EventSink（ADR 0024 I/O 边缘可注入接口）：emit 收集事件、list-like 供断言——作 sink 参数注入。** (1 connections) — `engines/novaact/tests/test_interrupt_model.py`
- **假 sink：收集 _run_step/_run_scenario 经 sink.emit 吐的事件供断言（作 sink 参数注入）。** (1 connections) — `engines/novaact/tests/test_interrupt_model.py`

## Relationships

- [Flag-only Interrupt Model](Flag-only_Interrupt_Model.md) (2 shared connections)
- [Test Fixtures And Env](Test_Fixtures_And_Env.md) (1 shared connections)

## Source Files

- `engines/novaact/tests/test_interrupt_model.py`

## Audit Trail

- EXTRACTED: 11 (100%)
- INFERRED: 0 (0%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*