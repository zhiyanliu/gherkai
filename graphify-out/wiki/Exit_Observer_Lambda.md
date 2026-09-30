# Exit Observer Lambda

> 30 nodes · cohesion 0.09

## Key Concepts

- **reconciler.py** (17 connections) — `deploy_aws/gherkai_deploy_aws/lambdas/reconciler.py`
- **exit_observer.py** (9 connections) — `deploy_aws/gherkai_deploy_aws/lambdas/exit_observer.py`
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
- **退出观察者 Lambda（ADR 0034，机制二 cloud 落地）：ECS Task STOPPED 事件 → 写 task_exited。…** (1 connections) — `deploy_aws/gherkai_deploy_aws/lambdas/exit_observer.py`
- **从 STOPPED event 的 detail 拿 (run_id, scope_id, exit_code, timed_out, reason)。…** (1 connections) — `deploy_aws/gherkai_deploy_aws/lambdas/exit_observer.py`
- **本 run 是否由云端推进器管（ADR 0034 端到端 cloud 1b：`detached` 标记在 runs 表 STATE item 上）。…** (1 connections) — `deploy_aws/gherkai_deploy_aws/lambdas/exit_observer.py`
- **构造 DdbEventLog（Lambda 组合根：读 env 造 boto3 表资源注入 core adapter）。** (1 connections) — `deploy_aws/gherkai_deploy_aws/lambdas/exit_observer.py`
- **EventBridge ECS STOPPED 事件入口。写本 task 的 task_exited。** (1 connections) — `deploy_aws/gherkai_deploy_aws/lambdas/exit_observer.py`
- **reconciler Lambda（ADR 0034）：DDB events 表 Stream 变化 → reconcile.tick 推进一步。…** (1 connections) — `deploy_aws/gherkai_deploy_aws/lambdas/reconciler.py`
- **超时处置（ADR 0034「job timeout」节的云端后端一侧）：仍 running 才动手——ListTasks(startedBy=run_id)…** (1 connections) — `deploy_aws/gherkai_deploy_aws/lambdas/reconciler.py`
- **防御性超时扫（ADR 0034「job timeout」节 claimed_at ②，Scheduler 的双保险）：任何 tick 顺带对 RUNNING…** (1 connections) — `deploy_aws/gherkai_deploy_aws/lambdas/reconciler.py`
- **本 run 各引擎的 worker task-def **revision ARN**（ADR 0038「读侧兼容口径」）。 ① definition 带…** (1 connections) — `deploy_aws/gherkai_deploy_aws/lambdas/reconciler.py`
- **从 DDB Stream records 提取涉及的 run_id 集（PK=run_id#scope_id，取 # 前段）。去重——一个 batch…** (1 connections) — `deploy_aws/gherkai_deploy_aws/lambdas/reconciler.py`
- *... and 5 more nodes in this community*

## Relationships

- [Cloud Launcher and EventLog](Cloud_Launcher_and_EventLog.md) (5 shared connections)
- [Reconcile Tick and Report](Reconcile_Tick_and_Report.md) (4 shared connections)
- [Lambda Handler Event Tests](Lambda_Handler_Event_Tests.md) (2 shared connections)
- [CDK App & Backend Stack](CDK_App_%26_Backend_Stack.md) (2 shared connections)
- [DynamoDB Run Store](DynamoDB_Run_Store.md) (1 shared connections)
- [Core Adapters Documentation](Core_Adapters_Documentation.md) (1 shared connections)

## Source Files

- `deploy_aws/gherkai_deploy_aws/lambdas/exit_observer.py`
- `deploy_aws/gherkai_deploy_aws/lambdas/reconciler.py`

## Audit Trail

- EXTRACTED: 53 (96%)
- INFERRED: 2 (4%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*