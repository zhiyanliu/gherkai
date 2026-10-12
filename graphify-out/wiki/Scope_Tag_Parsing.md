# Scope Tag Parsing

> 7 nodes · cohesion 0.29

## Key Concepts

- **scope seam（tag 分组 + engine 校验）** (6 connections) — `docs/adr/0025-plan-module-feature-to-jobs.md`
- **id 派生（scopeId / scenarioId 关联键）** (3 connections) — `docs/adr/0025-plan-module-feature-to-jobs.md`
- **uri 互异契约（重复 uri → 报错）** (2 connections) — `docs/adr/0025-plan-module-feature-to-jobs.md`
- **engine 解析（scope 级）** (1 connections) — `docs/adr/0025-plan-module-feature-to-jobs.md`
- **一个 scenario 多个 @scope 值 → 报错** (1 connections) — `docs/adr/0025-plan-module-feature-to-jobs.md`
- **scope 全局命名空间（跨文件合并，撞名 warning）** (1 connections) — `docs/adr/0025-plan-module-feature-to-jobs.md`
- **timeout 解析（@timeout:N → Job.timeoutS）** (1 connections) — `docs/adr/0025-plan-module-feature-to-jobs.md`

## Relationships

- [Engine Port And Job Plan](Engine_Port_And_Job_Plan.md) (2 shared connections)
- [DynamoDB Events Transport](DynamoDB_Events_Transport.md) (1 shared connections)

## Source Files

- `docs/adr/0025-plan-module-feature-to-jobs.md`

## Audit Trail

- EXTRACTED: 9 (100%)
- INFERRED: 0 (0%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*