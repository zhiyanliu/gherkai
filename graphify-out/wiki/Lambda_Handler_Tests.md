# Lambda Handler Tests

> 31 nodes · cohesion 0.06

## Key Concepts

- **test_lambda_handlers.py** (74 connections) — `deploy_aws/tests/test_lambda_handlers.py`
- **test_build_cap_defaults_to_one_when_env_absent()** (3 connections) — `deploy_aws/tests/test_lambda_handlers.py`
- **test_build_clamps_meta_max_concurrency_to_cap()** (3 connections) — `deploy_aws/tests/test_lambda_handlers.py`
- **test_build_defaults_to_one_when_meta_missing()** (3 connections) — `deploy_aws/tests/test_lambda_handlers.py`
- **test_build_raises_when_legacy_definition_unresolvable()** (3 connections) — `deploy_aws/tests/test_lambda_handlers.py`
- **test_build_reuses_its_own_handles_and_builds_no_new_client()** (3 connections) — `deploy_aws/tests/test_lambda_handlers.py`
- **test_build_takes_meta_max_concurrency_under_cap()** (3 connections) — `deploy_aws/tests/test_lambda_handlers.py`
- **test_scan_overdue_timeouts_only_over_budget()** (3 connections) — `deploy_aws/tests/test_lambda_handlers.py`
- **test_timeout_watch_conflict_is_idempotent()** (3 connections) — `deploy_aws/tests/test_lambda_handlers.py`
- **test_extract_missing_env_returns_none()** (2 connections) — `deploy_aws/tests/test_lambda_handlers.py`
- **test_handler_skips_when_no_run_id()** (2 connections) — `deploy_aws/tests/test_lambda_handlers.py`
- **test_kicker_routes_timeout_scope_payload()** (2 connections) — `deploy_aws/tests/test_lambda_handlers.py`
- **test_kicker_timeout_path_skips_tick_when_not_detached()** (2 connections) — `deploy_aws/tests/test_lambda_handlers.py`
- **test_starter_run_ids_empty_when_neither()** (2 connections) — `deploy_aws/tests/test_lambda_handlers.py`
- **test_starter_run_ids_from_direct_kick()** (2 connections) — `deploy_aws/tests/test_lambda_handlers.py`
- **test_timeout_watch_creates_one_time_schedule()** (2 connections) — `deploy_aws/tests/test_lambda_handlers.py`
- **Lambda handler 事件解析测试（ADR 0034 P4b）：退出观察者 _extract + reconciler…** (1 connections) — `deploy_aws/tests/test_lambda_handlers.py`
- **② 直接 invoke 踢一脚（status --wait 接力）：payload {"run_id": ...}——真测抓到的 bug： 原启动器只认…** (1 connections) — `deploy_aws/tests/test_lambda_handlers.py`
- **既无 Records 又无 run_id（如错误 payload）→ 空集（启动器 no-op、不崩）。** (1 connections) — `deploy_aws/tests/test_lambda_handlers.py`
- **同名已在（同 run+scope 重复 arm）→ ConflictException 吞掉视作已武装（幂等）。** (1 connections) — `deploy_aws/tests/test_lambda_handlers.py`
- **Scheduler 到点 invoke（payload {"run_id","timeout_scope"}）→ 先超时处置、再照常 tick（强制 tick…** (1 connections) — `deploy_aws/tests/test_lambda_handlers.py`
- **_build 判非 detached（返回 None）时也进 prebuilt：tick 不再白装配一次、整体 no-op。** (1 connections) — `deploy_aws/tests/test_lambda_handlers.py`
- **防御扫（claimed_at ②）只处置「超预算+余量」的 RUNNING job：过期的进处置、未到期/无 claimed_at 的不碰。** (1 connections) — `deploy_aws/tests/test_lambda_handlers.py`
- **`_build` 的三层 store 全用它自己已建的那批句柄装配——compose 里建句柄的两个钩子在此一次都不该执行。 这条同时是「region…** (1 connections) — `deploy_aws/tests/test_lambda_handlers.py`
- **definition 声明 ≤ cap → 按 definition 走（打通前云端后端静默忽略提交侧声明，是可用性缺陷）。** (1 connections) — `deploy_aws/tests/test_lambda_handlers.py`
- *... and 6 more nodes in this community*

## Relationships

- [Job Domain Models](Job_Domain_Models.md) (16 shared connections)
- [Stream Record Parsing Tests](Stream_Record_Parsing_Tests.md) (11 shared connections)
- [ECS Exit Code Extraction](ECS_Exit_Code_Extraction.md) (9 shared connections)
- [ECS Timeout Handling Tests](ECS_Timeout_Handling_Tests.md) (8 shared connections)
- [Finished Run Idempotence](Finished_Run_Idempotence.md) (4 shared connections)
- [Worker Task Def Resolution](Worker_Task_Def_Resolution.md) (4 shared connections)
- [Run ID Extraction](Run_ID_Extraction.md) (3 shared connections)
- [Task List Pagination](Task_List_Pagination.md) (3 shared connections)
- [Cloud Store Adapters](Cloud_Store_Adapters.md) (2 shared connections)
- [Exit Observer Lambda](Exit_Observer_Lambda.md) (1 shared connections)
- [Reconciler Lambda](Reconciler_Lambda.md) (1 shared connections)
- [Event Log Adapters](Event_Log_Adapters.md) (1 shared connections)

## Source Files

- `deploy_aws/tests/test_lambda_handlers.py`

## Audit Trail

- EXTRACTED: 97 (100%)
- INFERRED: 0 (0%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*