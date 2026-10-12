# Exit Observer Lambda

> 40 nodes · cohesion 0.08

## Key Concepts

- **reconciler.py** (17 connections) — `deploy_aws/gherkai_deploy_aws/lambdas/reconciler.py`
- **exit_observer.py** (9 connections) — `deploy_aws/gherkai_deploy_aws/lambdas/exit_observer.py`
- **EventBridgeTimeoutWatch** (9 connections) — `deploy_aws/gherkai_deploy_aws/lambdas/reconciler.py`
- **_build()** (8 connections) — `deploy_aws/gherkai_deploy_aws/lambdas/reconciler.py`
- **_tick_runs()** (8 connections) — `deploy_aws/gherkai_deploy_aws/lambdas/reconciler.py`
- **_handle_timeout()** (6 connections) — `deploy_aws/gherkai_deploy_aws/lambdas/reconciler.py`
- **kicker_handler()** (6 connections) — `deploy_aws/gherkai_deploy_aws/lambdas/reconciler.py`
- **handler()** (5 connections) — `deploy_aws/gherkai_deploy_aws/lambdas/exit_observer.py`
- **exit_from_task()** (5 connections) — `deploy_aws/gherkai_deploy_aws/lambdas/reconciler.py`
- **_event_log()** (4 connections) — `deploy_aws/gherkai_deploy_aws/lambdas/exit_observer.py`
- **_extract()** (4 connections) — `deploy_aws/gherkai_deploy_aws/lambdas/exit_observer.py`
- **_is_detached()** (4 connections) — `deploy_aws/gherkai_deploy_aws/lambdas/exit_observer.py`
- **handler()** (4 connections) — `deploy_aws/gherkai_deploy_aws/lambdas/reconciler.py`
- **_scan_overdue_timeouts()** (4 connections) — `deploy_aws/gherkai_deploy_aws/lambdas/reconciler.py`
- **_resolve_worker_task_defs()** (3 connections) — `deploy_aws/gherkai_deploy_aws/lambdas/reconciler.py`
- **_run_ids_from_runs_stream()** (3 connections) — `deploy_aws/gherkai_deploy_aws/lambdas/reconciler.py`
- **_run_ids_from_stream()** (3 connections) — `deploy_aws/gherkai_deploy_aws/lambdas/reconciler.py`
- **_task_scope_id()** (3 connections) — `deploy_aws/gherkai_deploy_aws/lambdas/reconciler.py`
- **BackendStack._reconcile_lambdas 事件链** (3 connections) — `deploy_aws/DEVELOPMENT.md`
- **.arm()** (2 connections) — `deploy_aws/gherkai_deploy_aws/lambdas/reconciler.py`
- **.schedule_name()** (2 connections) — `deploy_aws/gherkai_deploy_aws/lambdas/reconciler.py`
- **退出观察者 Lambda（ADR 0034，机制二 cloud 落地）：ECS Task STOPPED 事件 → 写 task_exited。…** (1 connections) — `deploy_aws/gherkai_deploy_aws/lambdas/exit_observer.py`
- **从 STOPPED event 的 detail 拿 (run_id, scope_id, exit_code, timed_out, reason)。…** (1 connections) — `deploy_aws/gherkai_deploy_aws/lambdas/exit_observer.py`
- **本 run 是否由云端推进器管（ADR 0034 端到端 cloud 1b：`detached` 标记在 runs 表 STATE item 上）。…** (1 connections) — `deploy_aws/gherkai_deploy_aws/lambdas/exit_observer.py`
- **构造 DdbEventLog（Lambda 组合根：读 env 造 boto3 表资源注入 core adapter）。** (1 connections) — `deploy_aws/gherkai_deploy_aws/lambdas/exit_observer.py`
- *... and 15 more nodes in this community*

## Relationships

- [Reconcile Tick & Report Finalize](Reconcile_Tick_%26_Report_Finalize.md) (3 shared connections)
- [Lambda Handler Event Parsing Tests](Lambda_Handler_Event_Parsing_Tests.md) (2 shared connections)
- [DynamoDB Event Log](DynamoDB_Event_Log.md) (2 shared connections)
- [Cloud Reconcile Launcher Tests](Cloud_Reconcile_Launcher_Tests.md) (2 shared connections)
- [Cloud Launcher & Fargate Adapters](Cloud_Launcher_%26_Fargate_Adapters.md) (2 shared connections)
- [Job/Scenario Explain Model](Job-Scenario_Explain_Model.md) (1 shared connections)
- [Backend CDK Stack Constructs](Backend_CDK_Stack_Constructs.md) (1 shared connections)

## Source Files

- `deploy_aws/DEVELOPMENT.md`
- `deploy_aws/gherkai_deploy_aws/lambdas/exit_observer.py`
- `deploy_aws/gherkai_deploy_aws/lambdas/reconciler.py`

## Audit Trail

- EXTRACTED: 63 (88%)
- INFERRED: 9 (12%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*