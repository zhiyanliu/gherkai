# Exit Observer Lambda

> 10 nodes · cohesion 0.27

## Key Concepts

- **exit_observer.py** (8 connections) — `deploy_aws/gherkai_deploy_aws/lambdas/exit_observer.py`
- **handler()** (5 connections) — `deploy_aws/gherkai_deploy_aws/lambdas/exit_observer.py`
- **_event_log()** (4 connections) — `deploy_aws/gherkai_deploy_aws/lambdas/exit_observer.py`
- **_is_detached()** (4 connections) — `deploy_aws/gherkai_deploy_aws/lambdas/exit_observer.py`
- **_extract()** (3 connections) — `deploy_aws/gherkai_deploy_aws/lambdas/exit_observer.py`
- **退出观察者 Lambda（ADR 0034，机制二 cloud 落地）：ECS Task STOPPED 事件 → 写 task_exited。…** (1 connections) — `deploy_aws/gherkai_deploy_aws/lambdas/exit_observer.py`
- **从 STOPPED event 的 detail 拿 (run_id, scope_id, exit_code, timed_out)。…** (1 connections) — `deploy_aws/gherkai_deploy_aws/lambdas/exit_observer.py`
- **本 run 是否由云端推进器管（ADR 0034 端到端 cloud 1b：`detached` 标记在 runs 表 STATE item 上）。…** (1 connections) — `deploy_aws/gherkai_deploy_aws/lambdas/exit_observer.py`
- **构造 DdbEventLog（Lambda 组合根：读 env 造 boto3 表资源注入 core adapter）。** (1 connections) — `deploy_aws/gherkai_deploy_aws/lambdas/exit_observer.py`
- **EventBridge ECS STOPPED 事件入口。写本 task 的 task_exited。** (1 connections) — `deploy_aws/gherkai_deploy_aws/lambdas/exit_observer.py`

## Relationships

- [Lambda Handler Event Parsing](Lambda_Handler_Event_Parsing.md) (1 shared connections)
- [Reconciler Lambda & Timeouts](Reconciler_Lambda_%26_Timeouts.md) (1 shared connections)
- [ADR Index & Dev Docs](ADR_Index_%26_Dev_Docs.md) (1 shared connections)
- [Cloud Launcher & DDB EventLog](Cloud_Launcher_%26_DDB_EventLog.md) (1 shared connections)
- [DynamoDB RunStore Conditional Writes](DynamoDB_RunStore_Conditional_Writes.md) (1 shared connections)

## Source Files

- `deploy_aws/gherkai_deploy_aws/lambdas/exit_observer.py`

## Audit Trail

- EXTRACTED: 15 (88%)
- INFERRED: 2 (12%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*