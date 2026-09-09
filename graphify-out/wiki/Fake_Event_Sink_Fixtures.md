# Fake Event Sink Fixtures

> 12 nodes · cohesion 0.17

## Key Concepts

- **_FakeSink** (8 connections) — `engines/novaact/tests/test_interrupt_model.py`
- **captured()** (4 connections) — `engines/novaact/tests/test_interrupt_model.py`
- **_reset_stop()** (3 connections) — `engines/novaact/tests/test_interrupt_model.py`
- **fixture** (2 connections)
- **.emit()** (1 connections) — `engines/novaact/tests/test_interrupt_model.py`
- **.__getitem__()** (1 connections) — `engines/novaact/tests/test_interrupt_model.py`
- **.__init__()** (1 connections) — `engines/novaact/tests/test_interrupt_model.py`
- **.__iter__()** (1 connections) — `engines/novaact/tests/test_interrupt_model.py`
- **.__len__()** (1 connections) — `engines/novaact/tests/test_interrupt_model.py`
- **每个用例前后清 _stop（模块级单例，避免用例间串扰）。** (1 connections) — `engines/novaact/tests/test_interrupt_model.py`
- **假 EventSink（ADR 0024 I/O 边缘可注入接口）：emit 收集事件、list-like 供断言——作 sink 参数注入。** (1 connections) — `engines/novaact/tests/test_interrupt_model.py`
- **假 sink：收集 _run_step/_run_scenario 经 sink.emit 吐的事件供断言（作 sink 参数注入）。** (1 connections) — `engines/novaact/tests/test_interrupt_model.py`

## Relationships

- [Worker Interrupt Model](Worker_Interrupt_Model.md) (3 shared connections)

## Source Files

- `engines/novaact/tests/test_interrupt_model.py`

## Audit Trail

- EXTRACTED: 14 (100%)
- INFERRED: 0 (0%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*