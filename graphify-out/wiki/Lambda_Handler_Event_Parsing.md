# Lambda Handler Event Parsing

> 24 nodes · cohesion 0.11

## Key Concepts

- **test_lambda_handlers.py** (54 connections) — `deploy_aws/tests/test_lambda_handlers.py`
- **_stream_record()** (8 connections) — `deploy_aws/tests/test_lambda_handlers.py`
- **test_reconciler_ticks_detached_run()** (4 connections) — `deploy_aws/tests/test_lambda_handlers.py`
- **test_reconciler_writes_timestamps_in_compose_clock_format()** (4 connections) — `deploy_aws/tests/test_lambda_handlers.py`
- **test_run_ids_dedup_multi_scope_same_run()** (3 connections) — `deploy_aws/tests/test_lambda_handlers.py`
- **test_run_ids_scope_with_colon_not_hash()** (3 connections) — `deploy_aws/tests/test_lambda_handlers.py`
- **test_scan_overdue_timeouts_only_over_budget()** (3 connections) — `deploy_aws/tests/test_lambda_handlers.py`
- **test_handler_skips_when_no_run_id()** (2 connections) — `deploy_aws/tests/test_lambda_handlers.py`
- **test_kicker_routes_timeout_scope_payload()** (2 connections) — `deploy_aws/tests/test_lambda_handlers.py`
- **test_kicker_timeout_path_builds_once()** (2 connections) — `deploy_aws/tests/test_lambda_handlers.py`
- **test_run_ids_multi_run()** (2 connections) — `deploy_aws/tests/test_lambda_handlers.py`
- **test_run_ids_single()** (2 connections) — `deploy_aws/tests/test_lambda_handlers.py`
- **test_starter_run_ids_empty_when_neither()** (2 connections) — `deploy_aws/tests/test_lambda_handlers.py`
- **test_timeout_watch_creates_one_time_schedule()** (2 connections) — `deploy_aws/tests/test_lambda_handlers.py`
- **Lambda handler 事件解析测试（ADR 0034 P4b）：退出观察者 _extract + reconciler…** (1 connections) — `deploy_aws/tests/test_lambda_handlers.py`
- **scope_id 含 : （feature:行号）但不含 #——rsplit('#',1) 正确只切 run_id#scope 的分隔。** (1 connections) — `deploy_aws/tests/test_lambda_handlers.py`
- **既无 Records 又无 run_id（如错误 payload）→ 空集（启动器 no-op、不崩）。** (1 connections) — `deploy_aws/tests/test_lambda_handlers.py`
- **Scheduler 到点 invoke（payload {"run_id","timeout_scope"}）→ 先超时处置、再照常 tick（强制 tick…** (1 connections) — `deploy_aws/tests/test_lambda_handlers.py`
- **超时路径的组合根只装配一次（护栏）：_build 每次造 boto3 client + 读 META（可能连 S3 还原正文）， 处置与随后的 tick…** (1 connections) — `deploy_aws/tests/test_lambda_handlers.py`
- **防御扫（claimed_at ②）只处置「超预算+余量」的 RUNNING job：过期的进处置、未到期/无 claimed_at 的不碰。** (1 connections) — `deploy_aws/tests/test_lambda_handlers.py`
- **对偶（防「gate 恒真」的假绿）：detached run 照常推进——tick 真跑、CAS 抢到那个 pending job。** (1 connections) — `deploy_aws/tests/test_lambda_handlers.py`
- **推进器 Lambda 落库的时间戳格式 = `compose.now_iso`（三宿主一份时钟，ADR 0034「时钟也只一份」）。 曾在本文件自带…** (1 connections) — `deploy_aws/tests/test_lambda_handlers.py`
- **handler 对缺 run_id 的事件返回 skipped（不崩、不误处理别的 cluster 负载）。** (1 connections) — `deploy_aws/tests/test_lambda_handlers.py`
- **同 run 多 scope 的多条 stream record → 去重成一个 run_id（handler 每 run tick 一次）。** (1 connections) — `deploy_aws/tests/test_lambda_handlers.py`

## Relationships

- [Reconciler Concurrency Cap](Reconciler_Concurrency_Cap.md) (10 shared connections)
- [_stopped_detail](_stopped_detail.md) (7 shared connections)
- [Engine Ports & Adapters](Engine_Ports_%26_Adapters.md) (5 shared connections)
- [Job Timeout Handling](Job_Timeout_Handling.md) (5 shared connections)
- [Worker Task Def Resolution](Worker_Task_Def_Resolution.md) (4 shared connections)
- [Kicker Run ID Extraction](Kicker_Run_ID_Extraction.md) (3 shared connections)
- [Run State Rendering & Boto Guard](Run_State_Rendering_%26_Boto_Guard.md) (2 shared connections)
- [Exit Observer Lambda](Exit_Observer_Lambda.md) (1 shared connections)
- [Reconciler Lambda & Timeouts](Reconciler_Lambda_%26_Timeouts.md) (1 shared connections)
- [Cloud Launcher & DDB EventLog](Cloud_Launcher_%26_DDB_EventLog.md) (1 shared connections)
- [Direct Kick Invocation](Direct_Kick_Invocation.md) (1 shared connections)
- [Idempotent Timeout Arming](Idempotent_Timeout_Arming.md) (1 shared connections)

## Source Files

- `deploy_aws/tests/test_lambda_handlers.py`

## Audit Trail

- EXTRACTED: 74 (100%)
- INFERRED: 0 (0%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*