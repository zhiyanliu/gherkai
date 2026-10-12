# Stateless Run Advancement

> 13 nodes · cohesion 0.17

## Key Concepts

- **reconcile.tick（推进器共享入口）** (6 connections) — `docs/adr/0034-detached-batch-reconciler.md`
- **events 表（append-only 真值日志）** (3 connections) — `docs/adr/0034-detached-batch-reconciler.md`
- **机制四：CAS(pending→running) 控严格并发** (2 connections) — `docs/adr/0034-detached-batch-reconciler.md`
- **退出观察者（ECS STOPPED → task_exited）** (2 connections) — `docs/adr/0034-detached-batch-reconciler.md`
- **job timeout（两层声明 → definition 载体 → 三路 enforce）** (2 connections) — `docs/adr/0034-detached-batch-reconciler.md`
- **kicker Lambda（冷启动推进器）** (2 connections) — `docs/adr/0034-detached-batch-reconciler.md`
- **project（纯归约：events + baseline → RunState）** (2 connections) — `docs/adr/0034-detached-batch-reconciler.md`
- **隧道守护 TTL（按 definition 算）** (2 connections) — `docs/adr/0035-local-app-testing-via-tunnel.md`
- **清理 pass（退休 tag + 静默期 + 运行中 run 引用检查）** (2 connections) — `docs/adr/0038-worker-image-delivery.md`
- **运行时显式 revision（RunMeta.worker_task_defs）** (2 connections) — `docs/adr/0038-worker-image-delivery.md`
- **plan_next（纯决策：该启哪些 pending、是否 finalize）** (1 connections) — `docs/adr/0034-detached-batch-reconciler.md`
- **status --wait 接力推进** (1 connections) — `docs/adr/0034-detached-batch-reconciler.md`
- **机制一：task_exited 独立键空间** (1 connections) — `docs/adr/0034-detached-batch-reconciler.md`

## Relationships

- [Core Library Concepts & ADRs](Core_Library_Concepts_%26_ADRs.md) (1 shared connections)
- [Release & Versioning Concepts](Release_%26_Versioning_Concepts.md) (1 shared connections)

## Source Files

- `docs/adr/0034-detached-batch-reconciler.md`
- `docs/adr/0035-local-app-testing-via-tunnel.md`
- `docs/adr/0038-worker-image-delivery.md`

## Audit Trail

- EXTRACTED: 15 (100%)
- INFERRED: 0 (0%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*