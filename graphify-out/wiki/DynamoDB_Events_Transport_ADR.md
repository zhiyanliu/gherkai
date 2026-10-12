# DynamoDB Events Transport ADR

> 13 nodes · cohesion 0.18

## Key Concepts

- **DynamoDB 共享 events 表作 events-out 传输** (9 connections) — `docs/adr/0024-worker-core-protocol.md`
- **EventSink（可注入事件出口）** (4 connections) — `docs/adr/0024-worker-core-protocol.md`
- **events 表键设计 PK=run_id#scope_id, SK=seq** (4 connections) — `docs/adr/0024-worker-core-protocol.md`
- **seq = worker 进程内自增计数器** (3 connections) — `docs/adr/0024-worker-core-protocol.md`
- **读一致性（流式期 EC 游标 + 终读强一致）** (2 connections) — `docs/adr/0024-worker-core-protocol.md`
- **task_exited 事件（独立键空间）** (2 connections) — `docs/adr/0024-worker-core-protocol.md`
- **events item TTL 自动过期（7 天 expires_at）** (1 connections) — `docs/adr/0024-worker-core-protocol.md`
- **被拒方案：DynamoDB Streams（同步 run 语境）** (1 connections) — `docs/adr/0024-worker-core-protocol.md`
- **被拒方案：MSK（Kafka）** (1 connections) — `docs/adr/0024-worker-core-protocol.md`
- **被拒方案：SQS FIFO per-run 队列** (1 connections) — `docs/adr/0024-worker-core-protocol.md`
- **run_id + scope_id 经 env 注入 worker** (1 connections) — `docs/adr/0024-worker-core-protocol.md`
- **独立 events 表、不混入 RunStore 表** (1 connections) — `docs/adr/0024-worker-core-protocol.md`
- **红线：worker 只直写 events 表、绝不碰 RunState** (1 connections) — `docs/adr/0024-worker-core-protocol.md`

## Relationships

- [Engine Port & Job Planning](Engine_Port_%26_Job_Planning.md) (1 shared connections)
- [Scope Tag Parsing](Scope_Tag_Parsing.md) (1 shared connections)
- [Worker Termination Contract](Worker_Termination_Contract.md) (1 shared connections)

## Source Files

- `docs/adr/0024-worker-core-protocol.md`

## Audit Trail

- EXTRACTED: 17 (100%)
- INFERRED: 0 (0%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*