# Transient Missing Exit Code

> 2 nodes · cohesion 1.00

## Key Concepts

- **test_await_exit_code_transient_missing_then_stopped_reads_code()** (2 connections) — `core/tests/test_fargate_engine.py`
- **MISSING 只是瞬时（最终一致）→ 宽限内恢复可见并 STOPPED → 正常读到码，不误报。** (1 connections) — `core/tests/test_fargate_engine.py`

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