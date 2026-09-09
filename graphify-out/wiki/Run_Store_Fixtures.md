# Run Store Fixtures

> 3 nodes · cohesion 0.67

## Key Concepts

- **run_store()** (5 connections) — `core/tests/test_conditional_writes.py`
- **fixture** (1 connections)
- **两个 adapter 各来一遍（对拍）。local 用 tmp_path；ddb 用 moto aws fixture。** (1 connections) — `core/tests/test_conditional_writes.py`

## Relationships

- [Local Run Store](Local_Run_Store.md) (1 shared connections)
- [Boto Guard & S3 Offload](Boto_Guard_%26_S3_Offload.md) (1 shared connections)
- [Conditional Write Tests](Conditional_Write_Tests.md) (1 shared connections)

## Source Files

- `core/tests/test_conditional_writes.py`

## Audit Trail

- EXTRACTED: 5 (100%)
- INFERRED: 0 (0%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*