# Kicker Timeout No-Op Path

> 2 nodes · cohesion 1.00

## Key Concepts

- **test_kicker_timeout_path_skips_tick_when_not_detached()** (2 connections) — `deploy_aws/tests/test_lambda_handlers.py`
- **_build 判非 detached（返回 None）时也进 prebuilt：tick 不再白装配一次、整体 no-op。** (1 connections) — `deploy_aws/tests/test_lambda_handlers.py`

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