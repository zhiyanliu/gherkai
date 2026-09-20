# ECS Task Exit Extraction

> 16 nodes · cohesion 0.12

## Key Concepts

- **_stopped_detail()** (10 connections) — `deploy_aws/tests/test_lambda_handlers.py`
- **test_exit_observer_records_exit_for_detached_run()** (4 connections) — `deploy_aws/tests/test_lambda_handlers.py`
- **test_exit_observer_skips_non_detached_run()** (4 connections) — `deploy_aws/tests/test_lambda_handlers.py`
- **test_exit_from_task_is_shared_by_observer_and_timeout_handler()** (3 connections) — `deploy_aws/tests/test_lambda_handlers.py`
- **test_extract_missing_exitcode_becomes_platform_sentinel_with_reason()** (3 connections) — `deploy_aws/tests/test_lambda_handlers.py`
- **test_extract_missing_exitcode_without_any_reason_still_gets_sentinel()** (3 connections) — `deploy_aws/tests/test_lambda_handlers.py`
- **test_extract_timed_out_from_stopped_reason_sentinel()** (3 connections) — `deploy_aws/tests/test_lambda_handlers.py`
- **test_extract_nonzero_exit()** (2 connections) — `deploy_aws/tests/test_lambda_handlers.py`
- **test_extract_run_scope_exit()** (2 connections) — `deploy_aws/tests/test_lambda_handlers.py`
- **构造真实形状的 ECS STOPPED event detail（RunTask 注入的 env 原样在 overrides，真验坐实）。** (1 connections) — `deploy_aws/tests/test_lambda_handlers.py`
- **container 缺 exitCode 表示容器没能开始运行（TaskFailedToStart）→ 落 PLATFORM_FAILED_EXIT 哨兵 +…** (1 connections) — `deploy_aws/tests/test_lambda_handlers.py`
- **连 stopCode/stoppedReason 都没有也不写 None：哨兵 + 占位归因，绝不留无码退出记录。** (1 connections) — `deploy_aws/tests/test_lambda_handlers.py`
- **同步 cloud run 的 task 停 → 不写 task_exited（它无 body 属性，会击穿同步路径的 events Query 读端）。** (1 connections) — `deploy_aws/tests/test_lambda_handlers.py`
- **对偶：detached run 的 task 停 → 照常写 task_exited（机制二的链不能被分流废掉）。** (1 connections) — `deploy_aws/tests/test_lambda_handlers.py`
- **stoppedReason 含超时哨兵（超时处置的 StopTask reason 原样出现于此）→ timed_out=True （ADR 0034「job…** (1 connections) — `deploy_aws/tests/test_lambda_handlers.py`
- **同一 task 对象 → 观察者 _extract 与 exit_from_task 给出同一 (exit_code, timed_out,…** (1 connections) — `deploy_aws/tests/test_lambda_handlers.py`

## Relationships

- [Lambda Handler Tests](Lambda_Handler_Tests.md) (9 shared connections)
- [Run Metadata & S3 Offload](Run_Metadata_%26_S3_Offload.md) (2 shared connections)

## Source Files

- `deploy_aws/tests/test_lambda_handlers.py`

## Audit Trail

- EXTRACTED: 26 (100%)
- INFERRED: 0 (0%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*