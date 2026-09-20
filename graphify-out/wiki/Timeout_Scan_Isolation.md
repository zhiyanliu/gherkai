# Timeout Scan Isolation

> 3 nodes · cohesion 0.67

## Key Concepts

- **test_tick_runs_isolates_defensive_scan_failure()** (3 connections) — `deploy_aws/tests/test_lambda_handlers.py`
- **.run_id()** (2 connections) — `core/gherkai_core/model.py`
- **防御性超时扫抛异常不连坐：本次调用仍成功返回，同一批里其它 run 照常推进（同 revision 解析失败的逐 run 隔离）。** (1 connections) — `deploy_aws/tests/test_lambda_handlers.py`

## Relationships

- [Explain Rendering Tests](Explain_Rendering_Tests.md) (1 shared connections)
- [Lambda Handler Tests](Lambda_Handler_Tests.md) (1 shared connections)

## Source Files

- `core/gherkai_core/model.py`
- `deploy_aws/tests/test_lambda_handlers.py`

## Audit Trail

- EXTRACTED: 3 (75%)
- INFERRED: 1 (25%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*