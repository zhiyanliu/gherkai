# Local Store Preflight

> 2 nodes · cohesion 1.00

## Key Concepts

- **.preflight()** (2 connections) — `core/gherkai_core/adapters/report_store/local.py`
- **探活 no-op（ADR 0030 决定七）：本地文件后端无「桶不存在」问题，目录随写随建。** (1 connections) — `core/gherkai_core/adapters/report_store/local.py`

## Relationships

- [Report Refs & Results](Report_Refs_%26_Results.md) (1 shared connections)

## Source Files

- `core/gherkai_core/adapters/report_store/local.py`

## Audit Trail

- EXTRACTED: 2 (100%)
- INFERRED: 0 (0%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*