# Idempotent Timeout Arming

> 2 nodes · cohesion 1.00

## Key Concepts

- **test_timeout_watch_conflict_is_idempotent()** (3 connections) — `deploy_aws/tests/test_lambda_handlers.py`
- **同名已在（同 run+scope 重复 arm）→ ConflictException 吞掉视作已武装（幂等）。** (1 connections) — `deploy_aws/tests/test_lambda_handlers.py`

## Relationships

- [Engine Ports & Adapters](Engine_Ports_%26_Adapters.md) (1 shared connections)
- [Lambda Handler Event Parsing](Lambda_Handler_Event_Parsing.md) (1 shared connections)

## Source Files

- `deploy_aws/tests/test_lambda_handlers.py`

## Audit Trail

- EXTRACTED: 3 (100%)
- INFERRED: 0 (0%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*