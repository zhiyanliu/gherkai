# Detached Run Mechanisms

> 17 nodes · cohesion 0.15

## Key Concepts

- **reconcile.tick（四宿主一份的推进入口）** (6 connections) — `docs/adr/0034-detached-batch-reconciler.md`
- **CQRS + 无状态 reconciler 机制** (4 connections) — `docs/adr/0034-detached-batch-reconciler.md`
- **退出观察者（平台侧读 exitCode 写 task_exited）** (4 connections) — `docs/adr/0034-detached-batch-reconciler.md`
- **project()：纯归约全量重放投影** (4 connections) — `docs/adr/0034-detached-batch-reconciler.md`
- **detached 顶层标记（推进链只碰 detached run）** (3 connections) — `docs/adr/0034-detached-batch-reconciler.md`
- **events 表（append-only 真值日志）** (3 connections) — `docs/adr/0034-detached-batch-reconciler.md`
- **job timeout（definition 载体 + 三路推进器各自 enforce）** (3 connections) — `docs/adr/0034-detached-batch-reconciler.md`
- **RunState 物化读视图（单一读接口不变量）** (3 connections) — `docs/adr/0034-detached-batch-reconciler.md`
- **kicker Lambda（冷启动推进器）** (2 connections) — `docs/adr/0034-detached-batch-reconciler.md`
- **task_exited 独立键空间** (2 connections) — `docs/adr/0034-detached-batch-reconciler.md`
- **隧道宿主三形态与 definition 派生 TTL** (2 connections) — `docs/adr/0035-local-app-testing-via-tunnel.md`
- **TunnelProvider 可插拔口子（首实现 ngrok）** (2 connections) — `docs/adr/0035-local-app-testing-via-tunnel.md`
- **清理 pass（退休 tag + 静默期 + 运行中 run 引用检查）** (2 connections) — `docs/adr/0038-worker-image-delivery.md`
- **运行时显式 task-def revision（按 digest 引用）** (2 connections) — `docs/adr/0038-worker-image-delivery.md`
- **CAS(pending→running) 并发闸** (1 connections) — `docs/adr/0034-detached-batch-reconciler.md`
- **HWM + 状态机单调条件写** (1 connections) — `docs/adr/0034-detached-batch-reconciler.md`
- **plan_next()：纯决策提议动作** (1 connections) — `docs/adr/0034-detached-batch-reconciler.md`

## Relationships

- [Skill and Packaging Features](Skill_and_Packaging_Features.md) (3 shared connections)
- [Core Protocol Documentation](Core_Protocol_Documentation.md) (1 shared connections)
- [CLI Docs and ADRs](CLI_Docs_and_ADRs.md) (1 shared connections)

## Source Files

- `docs/adr/0034-detached-batch-reconciler.md`
- `docs/adr/0035-local-app-testing-via-tunnel.md`
- `docs/adr/0038-worker-image-delivery.md`

## Audit Trail

- EXTRACTED: 24 (96%)
- INFERRED: 1 (4%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*