# Worker Exit Code Mapping

> 2 nodes · cohesion 1.00

## Key Concepts

- **test_raise_for_worker_exit_maps_codes_with_fargate_label()** (3 connections) — `core/tests/test_fargate_engine.py`
- **码→异常的翻译已收进 `wire`（协议级、与 subprocess adapter 共用一份）：这里锁本 adapter 的调法…** (1 connections) — `core/tests/test_fargate_engine.py`

## Relationships

- [Wire Protocol Serialization](Wire_Protocol_Serialization.md) (1 shared connections)
- [Fargate Engine Tests](Fargate_Engine_Tests.md) (1 shared connections)

## Source Files

- `core/tests/test_fargate_engine.py`

## Audit Trail

- EXTRACTED: 3 (100%)
- INFERRED: 0 (0%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*