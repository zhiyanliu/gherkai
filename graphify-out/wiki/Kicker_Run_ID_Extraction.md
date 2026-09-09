# Kicker Run ID Extraction

> 5 nodes · cohesion 0.40

## Key Concepts

- **_runs_stream_record()** (3 connections) — `deploy_aws/tests/test_lambda_handlers.py`
- **test_starter_run_ids_both_sources()** (3 connections) — `deploy_aws/tests/test_lambda_handlers.py`
- **test_starter_run_ids_from_runs_stream()** (3 connections) — `deploy_aws/tests/test_lambda_handlers.py`
- **① runs 表 Stream：从 Keys.run_id 提取（runs PK=run_id 非复合）。** (1 connections) — `deploy_aws/tests/test_lambda_handlers.py`
- **Stream records + 直接 run_id 并存时都提取（健壮）。** (1 connections) — `deploy_aws/tests/test_lambda_handlers.py`

## Relationships

- [Lambda Handler Event Parsing](Lambda_Handler_Event_Parsing.md) (3 shared connections)

## Source Files

- `deploy_aws/tests/test_lambda_handlers.py`

## Audit Trail

- EXTRACTED: 7 (100%)
- INFERRED: 0 (0%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*