# Act Timeout & Signal Handling

> 15 nodes · cohesion 0.13

## Key Concepts

- **Nova worker flag-only 信号 handler** (9 connections) — `docs/adr/0024-worker-core-protocol.md`
- **act 有界返回（per-act timeout）** (3 connections) — `docs/adr/0024-worker-core-protocol.md`
- **act 边界安全点检测标志** (3 connections) — `docs/adr/0024-worker-core-protocol.md`
- **errorType 分类** (2 connections) — `docs/adr/0024-worker-core-protocol.md`
- **grace 硬约束（grace ≥ ACT_TIMEOUT_S + margin）** (2 connections) — `docs/adr/0024-worker-core-protocol.md`
- **ScheduleOpts.min_grace_s（core 只校验关系）** (2 connections) — `docs/adr/0024-worker-core-protocol.md`
- **泄漏兜底：AgentCore 原生 session TTL** (2 connections) — `docs/adr/0024-worker-core-protocol.md`
- **安全点按「单元完成度」判定 emit** (2 connections) — `docs/adr/0024-worker-core-protocol.md`
- **cdp_session.__exit__ 释放 AgentCore 会话** (1 connections) — `docs/adr/0024-worker-core-protocol.md`
- **建连早期误报 engine_error 根治** (1 connections) — `docs/adr/0024-worker-core-protocol.md`
- **handler 内零 I/O（只置标志 + 记信号号）** (1 connections) — `docs/adr/0024-worker-core-protocol.md`
- **组合根单一 NOVA_ACT_TIMEOUT_S 常量** (1 connections) — `docs/adr/0024-worker-core-protocol.md`
- **被拒方案：Nova asyncio 化消除 greenlet** (1 connections) — `docs/adr/0024-worker-core-protocol.md`
- **被拒方案：handler raise _Terminated** (1 connections) — `docs/adr/0024-worker-core-protocol.md`
- **SIGINT（Ctrl-C）纳入同一 flag-only handler** (1 connections) — `docs/adr/0024-worker-core-protocol.md`

## Relationships

- [Architecture ADR Decisions](Architecture_ADR_Decisions.md) (2 shared connections)
- [Termination & Engine Ports](Termination_%26_Engine_Ports.md) (1 shared connections)
- [DynamoDB Events Transport](DynamoDB_Events_Transport.md) (1 shared connections)

## Source Files

- `docs/adr/0024-worker-core-protocol.md`

## Audit Trail

- EXTRACTED: 17 (94%)
- INFERRED: 1 (6%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*