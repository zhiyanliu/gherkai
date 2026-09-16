# Lambda Handler Tests

> 39 nodes · cohesion 0.06

## Key Concepts

- **test_lambda_handlers.py** (70 connections) — `deploy_aws/tests/test_lambda_handlers.py`
- **_stopped_detail()** (10 connections) — `deploy_aws/tests/test_lambda_handlers.py`
- **test_exit_observer_records_exit_for_detached_run()** (4 connections) — `deploy_aws/tests/test_lambda_handlers.py`
- **test_exit_observer_skips_non_detached_run()** (4 connections) — `deploy_aws/tests/test_lambda_handlers.py`
- **test_exit_from_task_is_shared_by_observer_and_timeout_handler()** (3 connections) — `deploy_aws/tests/test_lambda_handlers.py`
- **test_extract_missing_exitcode_becomes_platform_sentinel_with_reason()** (3 connections) — `deploy_aws/tests/test_lambda_handlers.py`
- **test_extract_missing_exitcode_without_any_reason_still_gets_sentinel()** (3 connections) — `deploy_aws/tests/test_lambda_handlers.py`
- **test_extract_timed_out_from_stopped_reason_sentinel()** (3 connections) — `deploy_aws/tests/test_lambda_handlers.py`
- **test_scan_overdue_timeouts_only_over_budget()** (3 connections) — `deploy_aws/tests/test_lambda_handlers.py`
- **test_timeout_watch_conflict_is_idempotent()** (3 connections) — `deploy_aws/tests/test_lambda_handlers.py`
- **test_extract_missing_env_returns_none()** (2 connections) — `deploy_aws/tests/test_lambda_handlers.py`
- **test_extract_nonzero_exit()** (2 connections) — `deploy_aws/tests/test_lambda_handlers.py`
- **test_extract_run_scope_exit()** (2 connections) — `deploy_aws/tests/test_lambda_handlers.py`
- **test_handler_skips_when_no_run_id()** (2 connections) — `deploy_aws/tests/test_lambda_handlers.py`
- **test_kicker_routes_timeout_scope_payload()** (2 connections) — `deploy_aws/tests/test_lambda_handlers.py`
- **test_kicker_timeout_path_builds_once()** (2 connections) — `deploy_aws/tests/test_lambda_handlers.py`
- **test_kicker_timeout_path_skips_tick_when_not_detached()** (2 connections) — `deploy_aws/tests/test_lambda_handlers.py`
- **test_starter_run_ids_empty_when_neither()** (2 connections) — `deploy_aws/tests/test_lambda_handlers.py`
- **test_starter_run_ids_from_direct_kick()** (2 connections) — `deploy_aws/tests/test_lambda_handlers.py`
- **test_tick_runs_isolates_a_run_whose_worker_revision_cannot_be_resolved()** (2 connections) — `deploy_aws/tests/test_lambda_handlers.py`
- **test_timeout_watch_creates_one_time_schedule()** (2 connections) — `deploy_aws/tests/test_lambda_handlers.py`
- **Lambda handler 事件解析测试（ADR 0034 P4b）：退出观察者 _extract + reconciler…** (1 connections) — `deploy_aws/tests/test_lambda_handlers.py`
- **② 直接 invoke 踢一脚（status --wait 接力）：payload {"run_id": ...}——真测抓到的 bug： 原启动器只认…** (1 connections) — `deploy_aws/tests/test_lambda_handlers.py`
- **既无 Records 又无 run_id（如错误 payload）→ 空集（启动器 no-op、不崩）。** (1 connections) — `deploy_aws/tests/test_lambda_handlers.py`
- **同名已在（同 run+scope 重复 arm）→ ConflictException 吞掉视作已武装（幂等）。** (1 connections) — `deploy_aws/tests/test_lambda_handlers.py`
- *... and 14 more nodes in this community*

## Relationships

- [Stream Record Reconcile Tests](Stream_Record_Reconcile_Tests.md) (14 shared connections)
- [Detached Run Gates & Concurrency](Detached_Run_Gates_%26_Concurrency.md) (14 shared connections)
- [Job Explain & S3 Offload](Job_Explain_%26_S3_Offload.md) (8 shared connections)
- [Job Timeout Handling](Job_Timeout_Handling.md) (8 shared connections)
- [Runs Stream Record Extraction](Runs_Stream_Record_Extraction.md) (3 shared connections)
- [DynamoDB RunStore Adapter](DynamoDB_RunStore_Adapter.md) (2 shared connections)
- [ECS Exit Observer Lambda](ECS_Exit_Observer_Lambda.md) (1 shared connections)
- [Reconciler Lambda](Reconciler_Lambda.md) (1 shared connections)
- [Cloud Job Launcher](Cloud_Job_Launcher.md) (1 shared connections)
- [Cloud Boto3 Guards & EventLog](Cloud_Boto3_Guards_%26_EventLog.md) (1 shared connections)
- [AWS Test Fixtures](AWS_Test_Fixtures.md) (1 shared connections)

## Source Files

- `deploy_aws/tests/test_lambda_handlers.py`

## Audit Trail

- EXTRACTED: 100 (100%)
- INFERRED: 0 (0%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*