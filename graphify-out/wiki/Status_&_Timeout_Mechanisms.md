# Status & Timeout Mechanisms

> 21 nodes · cohesion 0.11

## Key Concepts

- **reconcile.tick（无状态推进一步，四宿主共用）** (8 connections) — `docs/adr/0034-detached-batch-reconciler.md`
- **job timeout（两层声明 → definition → 三路 enforce）** (5 connections) — `docs/adr/0034-detached-batch-reconciler.md`
- **Status enum（加 SKIPPED/ABORTED/PENDING/RUNNING）** (4 connections) — `docs/adr/0031-job-lifecycle-states-and-severity.md`
- **project（纯归约：events → RunState）** (4 connections) — `docs/adr/0034-detached-batch-reconciler.md`
- **_aggregate（run 级 status 聚合）** (3 connections) — `docs/adr/0031-job-lifecycle-states-and-severity.md`
- **_STATUS_SEVERITY 数值序** (3 connections) — `docs/adr/0031-job-lifecycle-states-and-severity.md`
- **StepSkipped 事件（step 级短路）** (3 connections) — `docs/adr/0031-job-lifecycle-states-and-severity.md`
- **TERMINAL_STATUSES（终态真源，取补）** (3 connections) — `docs/adr/0031-job-lifecycle-states-and-severity.md`
- **task_exited（独立键空间的退出事件）** (3 connections) — `docs/adr/0034-detached-batch-reconciler.md`
- **隧道宿主三形态 + TTL 兜底** (3 connections) — `docs/adr/0035-local-app-testing-via-tunnel.md`
- **stopTimeout=120 / grace 预算标定** (2 connections) — `docs/adr/0032-fargate-execution-environment.md`
- **CAS(pending→running) 并发闸** (2 connections) — `docs/adr/0034-detached-batch-reconciler.md`
- **HWM + 状态机单调条件写** (2 connections) — `docs/adr/0034-detached-batch-reconciler.md`
- **kicker Lambda（冷启动 + kickoff + 超时到点）** (2 connections) — `docs/adr/0034-detached-batch-reconciler.md`
- **TunnelProvider 口子（首个实现 ngrok）** (2 connections) — `docs/adr/0035-local-app-testing-via-tunnel.md`
- **_NON_VERDICT 过滤名单** (1 connections) — `docs/adr/0031-job-lifecycle-states-and-severity.md`
- **StepResult.shortcircuited（正交布尔）** (1 connections) — `docs/adr/0031-job-lifecycle-states-and-severity.md`
- **exit-observer Lambda（ECS STOPPED → task_exited）** (1 connections) — `docs/adr/0034-detached-batch-reconciler.md`
- **reconcile.Launcher（无状态路径注入口）** (1 connections) — `docs/adr/0034-detached-batch-reconciler.md`
- **plan_next（纯决策：该启哪些 job / 是否 finalize）** (1 connections) — `docs/adr/0034-detached-batch-reconciler.md`
- **reconciler Lambda（events Stream 主推进）** (1 connections) — `docs/adr/0034-detached-batch-reconciler.md`

## Relationships

- [Architecture Decision Records](Architecture_Decision_Records.md) (7 shared connections)
- [Backend Stack Decisions](Backend_Stack_Decisions.md) (2 shared connections)

## Source Files

- `docs/adr/0031-job-lifecycle-states-and-severity.md`
- `docs/adr/0032-fargate-execution-environment.md`
- `docs/adr/0034-detached-batch-reconciler.md`
- `docs/adr/0035-local-app-testing-via-tunnel.md`

## Audit Trail

- EXTRACTED: 30 (94%)
- INFERRED: 2 (6%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*