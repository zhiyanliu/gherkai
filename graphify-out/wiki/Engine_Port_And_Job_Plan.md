# Engine Port And Job Plan

> 7 nodes · cohesion 0.33

## Key Concepts

- **plan 模块（.feature → Job 列表）** (6 connections) — `docs/adr/0025-plan-module-feature-to-jobs.md`
- **Engine port（run_scope → WorkerHandle + Event 迭代器）** (4 connections) — `docs/adr/0024-worker-core-protocol.md`
- **FargateEngine adapter** (3 connections) — `docs/adr/0024-worker-core-protocol.md`
- **JobSource（可注入 job 入口）** (2 connections) — `docs/adr/0024-worker-core-protocol.md`
- **pipe 传输实现 die（worker I/O 边缘必改）** (2 connections) — `docs/adr/0024-worker-core-protocol.md`
- **Job（一个 scope = 一个会话边界）** (2 connections) — `docs/adr/0025-plan-module-feature-to-jobs.md`
- **select 谓词（scenario 筛选）** (1 connections) — `docs/adr/0025-plan-module-feature-to-jobs.md`

## Relationships

- [Worker Termination Contract](Worker_Termination_Contract.md) (2 shared connections)
- [Scope Tag Parsing](Scope_Tag_Parsing.md) (2 shared connections)
- [DynamoDB Events Transport](DynamoDB_Events_Transport.md) (1 shared connections)
- [Gherkin Parse Seam](Gherkin_Parse_Seam.md) (1 shared connections)

## Source Files

- `docs/adr/0024-worker-core-protocol.md`
- `docs/adr/0025-plan-module-feature-to-jobs.md`

## Audit Trail

- EXTRACTED: 11 (85%)
- INFERRED: 2 (15%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*