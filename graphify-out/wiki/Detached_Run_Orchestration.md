# Detached Run Orchestration

> 9 nodes · cohesion 0.22

## Key Concepts

- **project / plan_next（纯归约 + 纯决策）** (6 connections) — `docs/adr/0034-detached-batch-reconciler.md`
- **CAS(pending→running) 控严格并发** (3 connections) — `docs/adr/0034-detached-batch-reconciler.md`
- **job timeout（definition 载体 + 三路 enforce）** (3 connections) — `docs/adr/0034-detached-batch-reconciler.md`
- **kicker Lambda（冷启动 + 接力 kickoff）** (3 connections) — `docs/adr/0034-detached-batch-reconciler.md`
- **ScheduleOpts（并发/隔离/grace/重试/心跳旋钮）** (2 connections) — `docs/adr/0026-schedule-module.md`
- **detached 标记（Stream filter + handler 分流）** (1 connections) — `docs/adr/0034-detached-batch-reconciler.md`
- **HWM + 状态机单调条件写** (1 connections) — `docs/adr/0034-detached-batch-reconciler.md`
- **submit / status --wait 命令形态** (1 connections) — `docs/adr/0034-detached-batch-reconciler.md`
- **task_exited 独立键空间 + 平台侧退出观察者** (1 connections) — `docs/adr/0034-detached-batch-reconciler.md`

## Relationships

- [Schedule & Retry ADRs](Schedule_%26_Retry_ADRs.md) (1 shared connections)
- [Plan Module Seams](Plan_Module_Seams.md) (1 shared connections)
- [DynamoDB Storage Design](DynamoDB_Storage_Design.md) (1 shared connections)
- [Report Aggregation & Status](Report_Aggregation_%26_Status.md) (1 shared connections)
- [Report Store & Manifest](Report_Store_%26_Manifest.md) (1 shared connections)

## Source Files

- `docs/adr/0026-schedule-module.md`
- `docs/adr/0034-detached-batch-reconciler.md`

## Audit Trail

- EXTRACTED: 13 (100%)
- INFERRED: 0 (0%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*