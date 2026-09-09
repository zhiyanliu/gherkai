# Missing Task Env Handling

> 2 nodes · cohesion 1.00

## Key Concepts

- **test_extract_missing_env_returns_none()** (2 connections) — `deploy_aws/tests/test_lambda_handlers.py`
- **非本框架起的 task（env 无 RUN_ID/SCOPE_ID）→ (None, None, ...)，handler 会跳过。** (1 connections) — `deploy_aws/tests/test_lambda_handlers.py`

## Relationships

- [Lambda Handler Event Parsing](Lambda_Handler_Event_Parsing.md) (1 shared connections)

## Source Files

- `deploy_aws/tests/test_lambda_handlers.py`

## Audit Trail

- EXTRACTED: 2 (100%)
- INFERRED: 0 (0%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*