# Exit Observer Lambda

> 12 nodes · cohesion 0.23

## Key Concepts

- **exit_observer.py** (7 connections) — `deploy_aws/gherkai_deploy_aws/lambdas/exit_observer.py`
- **handler()** (5 connections) — `deploy_aws/gherkai_deploy_aws/lambdas/exit_observer.py`
- **exit_from_task()** (5 connections) — `deploy_aws/gherkai_deploy_aws/lambdas/reconciler.py`
- **_event_log()** (4 connections) — `deploy_aws/gherkai_deploy_aws/lambdas/exit_observer.py`
- **_extract()** (4 connections) — `deploy_aws/gherkai_deploy_aws/lambdas/exit_observer.py`
- **_is_detached()** (4 connections) — `deploy_aws/gherkai_deploy_aws/lambdas/exit_observer.py`
- **退出观察者 Lambda（ADR 0034，机制二 cloud 落地）：ECS Task STOPPED 事件 → 写 task_exited。…** (1 connections) — `deploy_aws/gherkai_deploy_aws/lambdas/exit_observer.py`
- **从 STOPPED event 的 detail 拿 (run_id, scope_id, exit_code, timed_out, reason)。…** (1 connections) — `deploy_aws/gherkai_deploy_aws/lambdas/exit_observer.py`
- **本 run 是否由云端推进器管（ADR 0034 端到端 cloud 1b：`detached` 标记在 runs 表 STATE item 上）。…** (1 connections) — `deploy_aws/gherkai_deploy_aws/lambdas/exit_observer.py`
- **构造 DdbEventLog（Lambda 组合根：读 env 造 boto3 表资源注入 core adapter）。** (1 connections) — `deploy_aws/gherkai_deploy_aws/lambdas/exit_observer.py`
- **EventBridge ECS STOPPED 事件入口。写本 task 的 task_exited。** (1 connections) — `deploy_aws/gherkai_deploy_aws/lambdas/exit_observer.py`
- **ECS task 对象 → 退出记录三元组 (exit_code, timed_out, reason)。**观察者与超时处置共用**（ADR 0034…** (1 connections) — `deploy_aws/gherkai_deploy_aws/lambdas/reconciler.py`

## Relationships

- [Reconciler Lambda](Reconciler_Lambda.md) (2 shared connections)
- [Lambda Handler Tests](Lambda_Handler_Tests.md) (1 shared connections)
- [DynamoDB Event Log](DynamoDB_Event_Log.md) (1 shared connections)
- [Run Metadata & S3 Offload](Run_Metadata_%26_S3_Offload.md) (1 shared connections)

## Source Files

- `deploy_aws/gherkai_deploy_aws/lambdas/exit_observer.py`
- `deploy_aws/gherkai_deploy_aws/lambdas/reconciler.py`

## Audit Trail

- EXTRACTED: 18 (90%)
- INFERRED: 2 (10%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*