# Consistent-Read Gap Warnings

> 2 nodes · cohesion 1.00

## Key Concepts

- **test_final_drain_logs_real_holes_under_consistent_read()** (2 connections) — `core/tests/test_fargate_engine.py`
- **终读是强一致读，其中的断号无从补、只记警告（不等、不停）。** (1 connections) — `core/tests/test_fargate_engine.py`

## Relationships

- [Fargate Engine Tests](Fargate_Engine_Tests.md) (1 shared connections)

## Source Files

- `core/tests/test_fargate_engine.py`

## Audit Trail

- EXTRACTED: 2 (100%)
- INFERRED: 0 (0%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*