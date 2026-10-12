# Cooperative Stop Design

> 8 nodes · cohesion 0.25

## Key Concepts

- **Nova worker flag-only 协作式停止** (9 connections) — `docs/adr/0024-worker-core-protocol.md`
- **建连早期误报 engine_error 根治** (1 connections) — `docs/adr/0024-worker-core-protocol.md`
- **handler 内零 I/O（只置标志 + 记信号号）** (1 connections) — `docs/adr/0024-worker-core-protocol.md`
- **安全点按「单元完成度」判定丢弃** (1 connections) — `docs/adr/0024-worker-core-protocol.md`
- **被拒方案：asyncio 化消除 greenlet** (1 connections) — `docs/adr/0024-worker-core-protocol.md`
- **被拒方案：handler raise _Terminated 穿透 with** (1 connections) — `docs/adr/0024-worker-core-protocol.md`
- **泄漏兜底：AgentCore 原生 session TTL** (1 connections) — `docs/adr/0024-worker-core-protocol.md`
- **SIGINT（Ctrl-C）纳入 flag-only handler** (1 connections) — `docs/adr/0024-worker-core-protocol.md`

## Relationships

- [Worker Termination Contract](Worker_Termination_Contract.md) (1 shared connections)
- [Stop Grace Timeouts](Stop_Grace_Timeouts.md) (1 shared connections)

## Source Files

- `docs/adr/0024-worker-core-protocol.md`

## Audit Trail

- EXTRACTED: 9 (100%)
- INFERRED: 0 (0%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*