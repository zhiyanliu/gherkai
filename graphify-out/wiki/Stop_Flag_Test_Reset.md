# Stop Flag Test Reset

> 2 nodes · cohesion 1.00

## Key Concepts

- **_reset_stop()** (3 connections) — `engines/novaact/tests/test_interrupt_model.py`
- **每个用例前后清 _stop（模块级单例，避免用例间串扰）。** (1 connections) — `engines/novaact/tests/test_interrupt_model.py`

## Relationships

- [Test Fixtures And Env](Test_Fixtures_And_Env.md) (1 shared connections)
- [Flag-only Interrupt Model](Flag-only_Interrupt_Model.md) (1 shared connections)

## Source Files

- `engines/novaact/tests/test_interrupt_model.py`

## Audit Trail

- EXTRACTED: 3 (100%)
- INFERRED: 0 (0%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*