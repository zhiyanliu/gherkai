# Per-Run Failure Isolation

> 2 nodes · cohesion 1.00

## Key Concepts

- **test_tick_runs_isolates_a_run_whose_worker_revision_cannot_be_resolved()** (2 connections) — `deploy_aws/tests/test_lambda_handlers.py`
- **兼容路径解析不出的 run 只跳过它自己、不连坐同批其它 run：events Stream 一个 batch 含多个 run，抛出去 = ESM…** (1 connections) — `deploy_aws/tests/test_lambda_handlers.py`

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