# Reconciler Lambda

> 25 nodes · cohesion 0.11

## Key Concepts

- **reconciler.py** (14 connections) — `deploy_aws/gherkai_deploy_aws/lambdas/reconciler.py`
- **EventBridgeTimeoutWatch** (9 connections) — `deploy_aws/gherkai_deploy_aws/lambdas/reconciler.py`
- **_build()** (8 connections) — `deploy_aws/gherkai_deploy_aws/lambdas/reconciler.py`
- **_handle_timeout()** (6 connections) — `deploy_aws/gherkai_deploy_aws/lambdas/reconciler.py`
- **kicker_handler()** (6 connections) — `deploy_aws/gherkai_deploy_aws/lambdas/reconciler.py`
- **handler()** (4 connections) — `deploy_aws/gherkai_deploy_aws/lambdas/reconciler.py`
- **_scan_overdue_timeouts()** (4 connections) — `deploy_aws/gherkai_deploy_aws/lambdas/reconciler.py`
- **_resolve_worker_task_defs()** (3 connections) — `deploy_aws/gherkai_deploy_aws/lambdas/reconciler.py`
- **_run_ids_from_runs_stream()** (3 connections) — `deploy_aws/gherkai_deploy_aws/lambdas/reconciler.py`
- **_run_ids_from_stream()** (3 connections) — `deploy_aws/gherkai_deploy_aws/lambdas/reconciler.py`
- **_task_scope_id()** (3 connections) — `deploy_aws/gherkai_deploy_aws/lambdas/reconciler.py`
- **.arm()** (2 connections) — `deploy_aws/gherkai_deploy_aws/lambdas/reconciler.py`
- **.schedule_name()** (2 connections) — `deploy_aws/gherkai_deploy_aws/lambdas/reconciler.py`
- **.__init__()** (1 connections) — `deploy_aws/gherkai_deploy_aws/lambdas/reconciler.py`
- **reconciler Lambda（ADR 0034）：DDB events 表 Stream 变化 → reconcile.tick 推进一步。…** (1 connections) — `deploy_aws/gherkai_deploy_aws/lambdas/reconciler.py`
- **job timeout 的云端到点触发器（ADR 0034「job timeout」节）：CloudLauncher 起 task 后 arm 一个…** (1 connections) — `deploy_aws/gherkai_deploy_aws/lambdas/reconciler.py`
- **超时处置（ADR 0034「job timeout」节 cloud 档）：仍 running 才动手——ListTasks(startedBy=run_id)…** (1 connections) — `deploy_aws/gherkai_deploy_aws/lambdas/reconciler.py`
- **防御性超时扫（ADR 0034「job timeout」节 claimed_at ②，Scheduler 的双保险）：任何 tick 顺带对 RUNNING…** (1 connections) — `deploy_aws/gherkai_deploy_aws/lambdas/reconciler.py`
- **本 run 各引擎的 worker task-def **revision ARN**（ADR 0038「读侧兼容口径」）。 ① definition 带…** (1 connections) — `deploy_aws/gherkai_deploy_aws/lambdas/reconciler.py`
- **cloud 组合根：读 env 造 boto3 + 装配（RunStore/EventLog/CloudLauncher +…** (1 connections) — `deploy_aws/gherkai_deploy_aws/lambdas/reconciler.py`
- **从 DDB Stream records 提取涉及的 run_id 集（PK=run_id#scope_id，取 # 前段）。去重——一个 batch…** (1 connections) — `deploy_aws/gherkai_deploy_aws/lambdas/reconciler.py`
- **提取 kicker 要 tick 的 run_id 集。两种 event 源（kicker 同时服务两者）： ① runs 表…** (1 connections) — `deploy_aws/gherkai_deploy_aws/lambdas/reconciler.py`
- **events 表 Stream 入口（reconciler 主推进）：worker PutItem / task_exited 触发 → 对涉及 run…** (1 connections) — `deploy_aws/gherkai_deploy_aws/lambdas/reconciler.py`
- **kicker（踢启器）入口——两个触发源：runs 表 Stream 的 **INSERT**（冷启动：submit create_run 写…** (1 connections) — `deploy_aws/gherkai_deploy_aws/lambdas/reconciler.py`
- **RunTask 注入的 env SCOPE_ID 原样在…** (1 connections) — `deploy_aws/gherkai_deploy_aws/lambdas/reconciler.py`

## Relationships

- [Reconciler Ports](Reconciler_Ports.md) (5 shared connections)
- [Cloud Job Launcher](Cloud_Job_Launcher.md) (3 shared connections)
- [ECS Exit Observer Lambda](ECS_Exit_Observer_Lambda.md) (2 shared connections)
- [Lambda Handler Tests](Lambda_Handler_Tests.md) (1 shared connections)
- [Cloud Boto3 Guards & EventLog](Cloud_Boto3_Guards_%26_EventLog.md) (1 shared connections)
- [Runtime Composition Root](Runtime_Composition_Root.md) (1 shared connections)

## Source Files

- `deploy_aws/gherkai_deploy_aws/lambdas/reconciler.py`

## Audit Trail

- EXTRACTED: 41 (89%)
- INFERRED: 5 (11%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*