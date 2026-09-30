# Engine Runtime Mechanisms

> 33 nodes · cohesion 0.06

## Key Concepts

- **schedule() 接口** (6 connections) — `docs/adr/0026-schedule-module.md`
- **worker 内建连重试 + 手写退避** (6 connections) — `docs/adr/0028-transient-network-ssl-resilience.md`
- **DynamoDB 共享 events 表（events-out 传输）** (5 connections) — `docs/adr/0024-worker-core-protocol.md`
- **Nova flag-only 信号 handler** (5 connections) — `docs/adr/0024-worker-core-protocol.md`
- **终止契约（三层分工）** (5 connections) — `docs/adr/0024-worker-core-protocol.md`
- **EventSink（事件 sink 可注入接口）** (3 connections) — `docs/adr/0024-worker-core-protocol.md`
- **FargateEngine adapter** (3 connections) — `docs/adr/0024-worker-core-protocol.md`
- **grace 硬约束与护栏** (3 connections) — `docs/adr/0024-worker-core-protocol.md`
- **事件归集三级归约（status/成本/墙钟）** (3 connections) — `docs/adr/0026-schedule-module.md`
- **act 有界返回（per-act timeout）** (2 connections) — `docs/adr/0024-worker-core-protocol.md`
- **事件流结束信号（内容完整 + 进程终止都要）** (2 connections) — `docs/adr/0024-worker-core-protocol.md`
- **泄漏兜底：AgentCore session TTL（不引入 core reaper）** (2 connections) — `docs/adr/0024-worker-core-protocol.md`
- **_heartbeat_wrap（静默 worker 心跳）** (2 connections) — `docs/adr/0026-schedule-module.md`
- **ScheduleOpts（治理旋钮）** (2 connections) — `docs/adr/0026-schedule-module.md`
- **job 墙钟超时兜底** (2 connections) — `docs/adr/0026-schedule-module.md`
- **EX_WORKER_NETWORK = 80（带外信号）** (2 connections) — `docs/adr/0028-transient-network-ssl-resilience.md`
- **被拒方案：asyncio 化消除 greenlet** (1 connections) — `docs/adr/0024-worker-core-protocol.md`
- **被拒方案：DynamoDB Streams（同步 run 语境）** (1 connections) — `docs/adr/0024-worker-core-protocol.md`
- **引擎经 --capabilities 自报 min_grace_s** (1 connections) — `docs/adr/0024-worker-core-protocol.md`
- **exitCode 落值延迟的有界宽限轮询** (1 connections) — `docs/adr/0024-worker-core-protocol.md`
- **handler 内零 I/O（只置标志）** (1 connections) — `docs/adr/0024-worker-core-protocol.md`
- **Midscene 有序显式 cleanup handler** (1 connections) — `docs/adr/0024-worker-core-protocol.md`
- **被拒方案：MSK（Kafka）** (1 connections) — `docs/adr/0024-worker-core-protocol.md`
- **worker 进程内自增 seq（单写者不变量）** (1 connections) — `docs/adr/0024-worker-core-protocol.md`
- **被拒方案：SQS FIFO per-run 队列** (1 connections) — `docs/adr/0024-worker-core-protocol.md`
- *... and 8 more nodes in this community*

## Relationships

- [Core Protocol Documentation](Core_Protocol_Documentation.md) (6 shared connections)

## Source Files

- `docs/adr/0024-worker-core-protocol.md`
- `docs/adr/0026-schedule-module.md`
- `docs/adr/0028-transient-network-ssl-resilience.md`

## Audit Trail

- EXTRACTED: 38 (100%)
- INFERRED: 0 (0%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*