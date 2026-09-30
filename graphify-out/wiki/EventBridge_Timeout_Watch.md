# EventBridge Timeout Watch

> 5 nodes · cohesion 0.50

## Key Concepts

- **EventBridgeTimeoutWatch** (9 connections) — `deploy_aws/gherkai_deploy_aws/lambdas/reconciler.py`
- **.arm()** (2 connections) — `deploy_aws/gherkai_deploy_aws/lambdas/reconciler.py`
- **.schedule_name()** (2 connections) — `deploy_aws/gherkai_deploy_aws/lambdas/reconciler.py`
- **.__init__()** (1 connections) — `deploy_aws/gherkai_deploy_aws/lambdas/reconciler.py`
- **job timeout 的云端到点触发器（ADR 0034「job timeout」节）：CloudLauncher 起 task 后 arm 一个…** (1 connections) — `deploy_aws/gherkai_deploy_aws/lambdas/reconciler.py`

## Relationships

- [Reconciler Lambda](Reconciler_Lambda.md) (2 shared connections)
- [Run Result Aggregation Tree](Run_Result_Aggregation_Tree.md) (1 shared connections)
- [Cloud Launcher](Cloud_Launcher.md) (1 shared connections)
- [SSM Path Naming](SSM_Path_Naming.md) (1 shared connections)

## Source Files

- `deploy_aws/gherkai_deploy_aws/lambdas/reconciler.py`

## Audit Trail

- EXTRACTED: 7 (70%)
- INFERRED: 3 (30%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*