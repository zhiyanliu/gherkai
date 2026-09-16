# Cloud Run State Mechanisms

> 10 nodes · cohesion 0.20

## Key Concepts

- **无状态 reconciler（CQRS 投影 + 推进）** (6 connections) — `docs/adr/0034-detached-batch-reconciler.md`
- **job timeout（两层声明 → definition 载体 → 三路推进器 enforce）** (3 connections) — `docs/adr/0034-detached-batch-reconciler.md`
- **机制四：CAS(pending→running) 控严格并发** (2 connections) — `docs/adr/0034-detached-batch-reconciler.md`
- **机制二：平台侧退出观察者（从 STOPPED 事件读 exitCode）** (2 connections) — `docs/adr/0034-detached-batch-reconciler.md`
- **RunState 物化读视图（唯一写者 = reconciler）** (2 connections) — `docs/adr/0034-detached-batch-reconciler.md`
- **隧道生命周期三形态宿主与 TTL** (2 connections) — `docs/adr/0035-local-app-testing-via-tunnel.md`
- **events 表（append-only 真值日志，写模型）** (1 connections) — `docs/adr/0034-detached-batch-reconciler.md`
- **机制三：HWM 条件写 + 状态机单调条件写** (1 connections) — `docs/adr/0034-detached-batch-reconciler.md`
- **kicker Lambda（runs 表 Stream 冷启动）** (1 connections) — `docs/adr/0034-detached-batch-reconciler.md`
- **机制一：task_exited 用独立键空间** (1 connections) — `docs/adr/0034-detached-batch-reconciler.md`

## Relationships

- [Architecture ADR Decisions](Architecture_ADR_Decisions.md) (1 shared connections)
- [Project Conventions Docs](Project_Conventions_Docs.md) (1 shared connections)
- [Architecture Decision Records](Architecture_Decision_Records.md) (1 shared connections)

## Source Files

- `docs/adr/0034-detached-batch-reconciler.md`
- `docs/adr/0035-local-app-testing-via-tunnel.md`

## Audit Trail

- EXTRACTED: 11 (92%)
- INFERRED: 1 (8%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*