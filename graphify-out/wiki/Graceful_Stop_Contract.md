# Graceful Stop Contract

> 6 nodes · cohesion 0.33

## Key Concepts

- **act 有界返回（per-act timeout）** (2 connections) — `docs/adr/0024-worker-core-protocol.md`
- **引擎经 --capabilities 自报 min_grace_s** (2 connections) — `docs/adr/0024-worker-core-protocol.md`
- **FargateWorkerHandle.stop → StopTask** (2 connections) — `docs/adr/0024-worker-core-protocol.md`
- **grace 不对称（subprocess 运行期传参 vs Fargate stopTimeout）** (2 connections) — `docs/adr/0024-worker-core-protocol.md`
- **grace 硬约束（grace ≥ ACT_TIMEOUT_S + margin）** (2 connections) — `docs/adr/0024-worker-core-protocol.md`
- **机制层：Engine adapter / WorkerHandle 把停翻成机制** (2 connections) — `docs/adr/0024-worker-core-protocol.md`

## Relationships

- [Cooperative Stop Design](Cooperative_Stop_Design.md) (1 shared connections)
- [Worker Termination Contract](Worker_Termination_Contract.md) (1 shared connections)

## Source Files

- `docs/adr/0024-worker-core-protocol.md`

## Audit Trail

- EXTRACTED: 7 (100%)
- INFERRED: 0 (0%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*