# Worker Termination Contract

> 6 nodes · cohesion 0.33

## Key Concepts

- **终止契约（core 请求 worker 优雅停止）** (6 connections) — `docs/adr/0024-worker-core-protocol.md`
- **exitCode 落值延迟与 MISSING 第三态** (3 connections) — `docs/adr/0024-worker-core-protocol.md`
- **事件流结束信号 / 存活判定迁移** (2 connections) — `docs/adr/0024-worker-core-protocol.md`
- **Midscene worker 有序显式 cleanup handler** (2 connections) — `docs/adr/0024-worker-core-protocol.md`
- **逻辑层：schedule 经 worker 句柄请求停（handle.stop）** (2 connections) — `docs/adr/0024-worker-core-protocol.md`
- **未来演进：显式 core→worker 控制通道** (1 connections) — `docs/adr/0024-worker-core-protocol.md`

## Relationships

- [Engine Port & Job Planning](Engine_Port_%26_Job_Planning.md) (2 shared connections)
- [DynamoDB Events Transport ADR](DynamoDB_Events_Transport_ADR.md) (1 shared connections)
- [Gherkin Parse Seam](Gherkin_Parse_Seam.md) (1 shared connections)
- [Cooperative Stop Design](Cooperative_Stop_Design.md) (1 shared connections)
- [Graceful Stop Contract](Graceful_Stop_Contract.md) (1 shared connections)

## Source Files

- `docs/adr/0024-worker-core-protocol.md`

## Audit Trail

- EXTRACTED: 9 (82%)
- INFERRED: 1 (9%)
- AMBIGUOUS: 1 (9%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*