# Reconciler Lambda & Timeouts

> 25 nodes · cohesion 0.12

## Key Concepts

- **reconciler.py** (15 connections) — `deploy_aws/gherkai_deploy_aws/lambdas/reconciler.py`
- **_build()** (12 connections) — `deploy_aws/gherkai_deploy_aws/lambdas/reconciler.py`
- **EventBridgeTimeoutWatch** (11 connections) — `deploy_aws/gherkai_deploy_aws/lambdas/reconciler.py`
- **_tick_runs()** (8 connections) — `deploy_aws/gherkai_deploy_aws/lambdas/reconciler.py`
- **kicker_handler()** (6 connections) — `deploy_aws/gherkai_deploy_aws/lambdas/reconciler.py`
- **_handle_timeout()** (4 connections) — `deploy_aws/gherkai_deploy_aws/lambdas/reconciler.py`
- **handler()** (4 connections) — `deploy_aws/gherkai_deploy_aws/lambdas/reconciler.py`
- **_scan_overdue_timeouts()** (4 connections) — `deploy_aws/gherkai_deploy_aws/lambdas/reconciler.py`
- **_resolve_worker_task_defs()** (3 connections) — `deploy_aws/gherkai_deploy_aws/lambdas/reconciler.py`
- **_run_ids_from_runs_stream()** (3 connections) — `deploy_aws/gherkai_deploy_aws/lambdas/reconciler.py`
- **_run_ids_from_stream()** (3 connections) — `deploy_aws/gherkai_deploy_aws/lambdas/reconciler.py`
- **.arm()** (2 connections) — `deploy_aws/gherkai_deploy_aws/lambdas/reconciler.py`
- **.schedule_name()** (2 connections) — `deploy_aws/gherkai_deploy_aws/lambdas/reconciler.py`
- **.__init__()** (1 connections) — `deploy_aws/gherkai_deploy_aws/lambdas/reconciler.py`
- **reconciler Lambda（ADR 0034）：DDB events 表 Stream 变化 → reconcile.tick 推进一步。…** (1 connections) — `deploy_aws/gherkai_deploy_aws/lambdas/reconciler.py`
- **超时处置（ADR 0034「job timeout」节 cloud 档）：仍 running 才动手——ListTasks(startedBy=run_id)…** (1 connections) — `deploy_aws/gherkai_deploy_aws/lambdas/reconciler.py`
- **防御性超时扫（ADR 0034「job timeout」节 claimed_at ②，Scheduler 的双保险）：任何 tick 顺带对 RUNNING…** (1 connections) — `deploy_aws/gherkai_deploy_aws/lambdas/reconciler.py`
- **本 run 各引擎的 worker task-def **revision ARN**（ADR 0038「读侧兼容口径」）。 ① definition 带…** (1 connections) — `deploy_aws/gherkai_deploy_aws/lambdas/reconciler.py`
- **cloud 组合根：读 env 造 boto3 + 装配（RunStore/EventLog/CloudLauncher +…** (1 connections) — `deploy_aws/gherkai_deploy_aws/lambdas/reconciler.py`
- **提取 kicker 要 tick 的 run_id 集。两种 event 源（kicker 同时服务两者）： ① runs 表…** (1 connections) — `deploy_aws/gherkai_deploy_aws/lambdas/reconciler.py`
- **从 DDB Stream records 提取涉及的 run_id 集（PK=run_id#scope_id，取 # 前段）。去重——一个 batch…** (1 connections) — `deploy_aws/gherkai_deploy_aws/lambdas/reconciler.py`
- **对每个 run tick 一步；done 则聚合收尾。reconciler（events Stream）与 kicker（runs Stream）共用。…** (1 connections) — `deploy_aws/gherkai_deploy_aws/lambdas/reconciler.py`
- **events 表 Stream 入口（reconciler 主推进）：worker PutItem / task_exited 触发 → 对涉及 run…** (1 connections) — `deploy_aws/gherkai_deploy_aws/lambdas/reconciler.py`
- **kicker（踢启器）入口——两个触发源：runs 表 Stream 的 **INSERT**（冷启动：submit create_run 写…** (1 connections) — `deploy_aws/gherkai_deploy_aws/lambdas/reconciler.py`
- **job timeout 的云端到点触发器（ADR 0034「job timeout」节）：CloudLauncher 起 task 后 arm 一个…** (1 connections) — `deploy_aws/gherkai_deploy_aws/lambdas/reconciler.py`

## Relationships

- [Run Result Verdict Model](Run_Result_Verdict_Model.md) (3 shared connections)
- [Cloud Launcher & DDB EventLog](Cloud_Launcher_%26_DDB_EventLog.md) (3 shared connections)
- [S3 Argument Offload](S3_Argument_Offload.md) (2 shared connections)
- [S3 ReportStore & Subprocess Engine](S3_ReportStore_%26_Subprocess_Engine.md) (2 shared connections)
- [Lambda Handler Event Parsing](Lambda_Handler_Event_Parsing.md) (1 shared connections)
- [Exit Observer Lambda](Exit_Observer_Lambda.md) (1 shared connections)
- [ADR Index & Dev Docs](ADR_Index_%26_Dev_Docs.md) (1 shared connections)
- [DynamoDB RunStore Conditional Writes](DynamoDB_RunStore_Conditional_Writes.md) (1 shared connections)
- [S3 ResultStore](S3_ResultStore.md) (1 shared connections)
- [Composition Root Wiring](Composition_Root_Wiring.md) (1 shared connections)
- [Reconcile Ports & Tick](Reconcile_Ports_%26_Tick.md) (1 shared connections)

## Source Files

- `deploy_aws/gherkai_deploy_aws/lambdas/reconciler.py`

## Audit Trail

- EXTRACTED: 40 (75%)
- INFERRED: 13 (25%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*