# Lambda Handler Tests

> 28 nodes · cohesion 0.08

## Key Concepts

- **test_lambda_handlers.py** (54 connections) — `deploy_aws/tests/test_lambda_handlers.py`
- **_runs_stream_record()** (3 connections) — `deploy_aws/tests/test_lambda_handlers.py`
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
- **既无 Records 又无 run_id（如错误 payload）→ 空集（启动器 no-op、不崩）。** (1 connections) — `deploy_aws/tests/test_lambda_handlers.py`
- **同名已在（同 run+scope 重复 arm）→ ConflictException 吞掉视作已武装（幂等）。** (1 connections) — `deploy_aws/tests/test_lambda_handlers.py`
- **Scheduler 到点 invoke（payload {"run_id","timeout_scope"}）→ 先超时处置、再照常 tick（强制 tick…** (1 connections) — `deploy_aws/tests/test_lambda_handlers.py`
- **超时路径的组合根只装配一次（护栏）：_build 每次造 boto3 client + 读 META（可能连 S3 还原正文）， 处置与随后的 tick…** (1 connections) — `deploy_aws/tests/test_lambda_handlers.py`
- **_build 判非 detached（返回 None）时也进 prebuilt：tick 不再白装配一次、整体 no-op。** (1 connections) — `deploy_aws/tests/test_lambda_handlers.py`
- **防御扫（claimed_at ②）只处置「超预算+余量」的 RUNNING job：过期的进处置、未到期/无 claimed_at 的不碰。** (1 connections) — `deploy_aws/tests/test_lambda_handlers.py`
- *... and 3 more nodes in this community*

## Relationships

- [Cloud Definition & SSM Tests](Cloud_Definition_%26_SSM_Tests.md) (10 shared connections)
- [Reconciler Trigger Tests](Reconciler_Trigger_Tests.md) (8 shared connections)
- [ECS Exit Observer Extraction](ECS_Exit_Observer_Extraction.md) (7 shared connections)
- [Engine Ports & Adapters](Engine_Ports_%26_Adapters.md) (6 shared connections)
- [Timeout Handling Tests](Timeout_Handling_Tests.md) (5 shared connections)
- [Exit Observer Lambda](Exit_Observer_Lambda.md) (1 shared connections)
- [Reconciler Lambda](Reconciler_Lambda.md) (1 shared connections)
- [SQLite Event Log](SQLite_Event_Log.md) (1 shared connections)
- [Run State Rendering](Run_State_Rendering.md) (1 shared connections)
- [Boto Guard & S3 Offload](Boto_Guard_%26_S3_Offload.md) (1 shared connections)
- [Cloud Env Fixture](Cloud_Env_Fixture.md) (1 shared connections)

## Source Files

- `deploy_aws/tests/test_lambda_handlers.py`

## Audit Trail

- EXTRACTED: 71 (100%)
- INFERRED: 0 (0%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*