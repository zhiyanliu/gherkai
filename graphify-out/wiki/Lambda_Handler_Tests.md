# Lambda Handler Tests

> 40 nodes · cohesion 0.05

## Key Concepts

- **test_lambda_handlers.py** (74 connections) — `deploy_aws/tests/test_lambda_handlers.py`
- **_runs_stream_record()** (3 connections) — `deploy_aws/tests/test_lambda_handlers.py`
- **test_build_cap_defaults_to_one_when_env_absent()** (3 connections) — `deploy_aws/tests/test_lambda_handlers.py`
- **test_build_clamps_meta_max_concurrency_to_cap()** (3 connections) — `deploy_aws/tests/test_lambda_handlers.py`
- **test_build_defaults_to_one_when_meta_missing()** (3 connections) — `deploy_aws/tests/test_lambda_handlers.py`
- **test_build_raises_when_legacy_definition_unresolvable()** (3 connections) — `deploy_aws/tests/test_lambda_handlers.py`
- **test_build_reuses_its_own_handles_and_builds_no_new_client()** (3 connections) — `deploy_aws/tests/test_lambda_handlers.py`
- **test_build_takes_meta_max_concurrency_under_cap()** (3 connections) — `deploy_aws/tests/test_lambda_handlers.py`
- **test_scan_overdue_timeouts_only_over_budget()** (3 connections) — `deploy_aws/tests/test_lambda_handlers.py`
- **test_starter_run_ids_both_sources()** (3 connections) — `deploy_aws/tests/test_lambda_handlers.py`
- **test_starter_run_ids_from_runs_stream()** (3 connections) — `deploy_aws/tests/test_lambda_handlers.py`
- **test_timeout_watch_conflict_is_idempotent()** (3 connections) — `deploy_aws/tests/test_lambda_handlers.py`
- **test_extract_missing_env_returns_none()** (2 connections) — `deploy_aws/tests/test_lambda_handlers.py`
- **test_handler_skips_when_no_run_id()** (2 connections) — `deploy_aws/tests/test_lambda_handlers.py`
- **test_kicker_routes_timeout_scope_payload()** (2 connections) — `deploy_aws/tests/test_lambda_handlers.py`
- **test_kicker_timeout_path_builds_once()** (2 connections) — `deploy_aws/tests/test_lambda_handlers.py`
- **test_kicker_timeout_path_skips_tick_when_not_detached()** (2 connections) — `deploy_aws/tests/test_lambda_handlers.py`
- **test_starter_run_ids_empty_when_neither()** (2 connections) — `deploy_aws/tests/test_lambda_handlers.py`
- **test_starter_run_ids_from_direct_kick()** (2 connections) — `deploy_aws/tests/test_lambda_handlers.py`
- **test_tick_runs_isolates_a_run_whose_worker_revision_cannot_be_resolved()** (2 connections) — `deploy_aws/tests/test_lambda_handlers.py`
- **test_timeout_watch_creates_one_time_schedule()** (2 connections) — `deploy_aws/tests/test_lambda_handlers.py`
- **Lambda handler 事件解析测试（ADR 0034 P4b）：退出观察者 _extract + reconciler…** (1 connections) — `deploy_aws/tests/test_lambda_handlers.py`
- **① runs 表 Stream：从 Keys.run_id 提取（runs PK=run_id 非复合）。** (1 connections) — `deploy_aws/tests/test_lambda_handlers.py`
- **② 直接 invoke 踢一脚（status --wait 接力）：payload {"run_id": ...}——真测抓到的 bug： 原启动器只认…** (1 connections) — `deploy_aws/tests/test_lambda_handlers.py`
- **Stream records + 直接 run_id 并存时都提取（健壮）。** (1 connections) — `deploy_aws/tests/test_lambda_handlers.py`
- *... and 15 more nodes in this community*

## Relationships

- [Run Metadata & S3 Offload](Run_Metadata_%26_S3_Offload.md) (26 shared connections)
- [Reconciler Stream Tests](Reconciler_Stream_Tests.md) (11 shared connections)
- [ECS Task Exit Extraction](ECS_Task_Exit_Extraction.md) (9 shared connections)
- [Finished Run Idempotency](Finished_Run_Idempotency.md) (4 shared connections)
- [Worker Revision Resolution](Worker_Revision_Resolution.md) (4 shared connections)
- [Run State Rendering](Run_State_Rendering.md) (3 shared connections)
- [Exit Observer Lambda](Exit_Observer_Lambda.md) (1 shared connections)
- [Reconciler Lambda](Reconciler_Lambda.md) (1 shared connections)
- [DynamoDB Event Log](DynamoDB_Event_Log.md) (1 shared connections)
- [Timeout Scan Isolation](Timeout_Scan_Isolation.md) (1 shared connections)
- [AWS Test Fixtures (moto)](AWS_Test_Fixtures_%28moto%29.md) (1 shared connections)

## Source Files

- `deploy_aws/tests/test_lambda_handlers.py`

## Audit Trail

- EXTRACTED: 103 (100%)
- INFERRED: 0 (0%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*