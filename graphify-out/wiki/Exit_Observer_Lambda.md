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

- [Lambda Handler Tests](Lambda_Handler_Tests.md) (1 shared connections)
- [Reconciler Lambda](Reconciler_Lambda.md) (1 shared connections)
- [Architecture Decision Records](Architecture_Decision_Records.md) (1 shared connections)
- [Cloud Launcher & DDB Event Log](Cloud_Launcher_%26_DDB_Event_Log.md) (1 shared connections)
- [Boto Guard & S3 Offload](Boto_Guard_%26_S3_Offload.md) (1 shared connections)

## Source Files

- `deploy_aws/gherkai_deploy_aws/lambdas/exit_observer.py`

## Audit Trail

- EXTRACTED: 15 (88%)
- INFERRED: 2 (12%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*