# ECS Exit Observer Extraction

> 12 nodes · cohesion 0.17

## Key Concepts

- **_stopped_detail()** (8 connections) — `deploy_aws/tests/test_lambda_handlers.py`
- **test_exit_observer_records_exit_for_detached_run()** (4 connections) — `deploy_aws/tests/test_lambda_handlers.py`
- **test_exit_observer_skips_non_detached_run()** (4 connections) — `deploy_aws/tests/test_lambda_handlers.py`
- **test_extract_missing_exitcode_is_none()** (3 connections) — `deploy_aws/tests/test_lambda_handlers.py`
- **test_extract_timed_out_from_stopped_reason_sentinel()** (3 connections) — `deploy_aws/tests/test_lambda_handlers.py`
- **test_extract_nonzero_exit()** (2 connections) — `deploy_aws/tests/test_lambda_handlers.py`
- **test_extract_run_scope_exit()** (2 connections) — `deploy_aws/tests/test_lambda_handlers.py`
- **构造真实形状的 ECS STOPPED event detail（RunTask 注入的 env 原样在 overrides，真验坐实）。** (1 connections) — `deploy_aws/tests/test_lambda_handlers.py`
- **同步 cloud run 的 task 停 → 不写 task_exited（它无 body 属性，会击穿同步路径的 events Query 读端）。** (1 connections) — `deploy_aws/tests/test_lambda_handlers.py`
- **对偶：detached run 的 task 停 → 照常写 task_exited（机制二的链不能被分流废掉）。** (1 connections) — `deploy_aws/tests/test_lambda_handlers.py`
- **container 缺 exitCode（宽限态）→ None（机制二保守）。** (1 connections) — `deploy_aws/tests/test_lambda_handlers.py`
- **stoppedReason 含超时哨兵（超时处置的 StopTask reason 原样出现于此）→ timed_out=True （ADR 0034「job…** (1 connections) — `deploy_aws/tests/test_lambda_handlers.py`

## Relationships

- [Lambda Handler Tests](Lambda_Handler_Tests.md) (7 shared connections)
- [Cloud Definition & SSM Tests](Cloud_Definition_%26_SSM_Tests.md) (2 shared connections)

## Source Files

- `deploy_aws/tests/test_lambda_handlers.py`

## Audit Trail

- EXTRACTED: 20 (100%)
- INFERRED: 0 (0%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*