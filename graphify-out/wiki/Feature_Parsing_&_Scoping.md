# Feature Parsing & Scoping

> 7 nodes · cohesion 0.29

## Key Concepts

- **plan() 接口** (5 connections) — `docs/adr/0025-plan-module-feature-to-jobs.md`
- **Job（scope = 会话边界）** (2 connections) — `docs/adr/0025-plan-module-feature-to-jobs.md`
- **parse seam（藏 gherkin-official）** (2 connections) — `docs/adr/0025-plan-module-feature-to-jobs.md`
- **scope seam（tag 分组 + engine/timeout 校验）** (2 connections) — `docs/adr/0025-plan-module-feature-to-jobs.md`
- **gherkin-official（Parser + Compiler）** (1 connections) — `docs/adr/0025-plan-module-feature-to-jobs.md`
- **id 派生（稳定 + 可追溯）** (1 connections) — `docs/adr/0025-plan-module-feature-to-jobs.md`
- **select 谓词（scenario 筛选）** (1 connections) — `docs/adr/0025-plan-module-feature-to-jobs.md`

## Relationships

- [Package Contributor Docs](Package_Contributor_Docs.md) (2 shared connections)

## Source Files

- `docs/adr/0025-plan-module-feature-to-jobs.md`

## Audit Trail

- EXTRACTED: 6 (75%)
- INFERRED: 2 (25%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*