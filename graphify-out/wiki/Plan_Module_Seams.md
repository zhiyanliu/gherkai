# Plan Module Seams

> 5 nodes · cohesion 0.40

## Key Concepts

- **plan(features, config, select) -> Job[]** (4 connections) — `docs/adr/0025-plan-module-feature-to-jobs.md`
- **scope seam（tag 分组 + engine/timeout 校验）** (3 connections) — `docs/adr/0025-plan-module-feature-to-jobs.md`
- **id 派生（scenarioId/scopeId 不透明、不 normalize）** (2 connections) — `docs/adr/0025-plan-module-feature-to-jobs.md`
- **parse seam（藏 gherkin-official）** (1 connections) — `docs/adr/0025-plan-module-feature-to-jobs.md`
- **select 谓词（scenario 筛选）** (1 connections) — `docs/adr/0025-plan-module-feature-to-jobs.md`

## Relationships

- [Report Aggregation & Status](Report_Aggregation_%26_Status.md) (1 shared connections)
- [Schedule & Retry ADRs](Schedule_%26_Retry_ADRs.md) (1 shared connections)
- [Detached Run Orchestration](Detached_Run_Orchestration.md) (1 shared connections)

## Source Files

- `docs/adr/0025-plan-module-feature-to-jobs.md`

## Audit Trail

- EXTRACTED: 6 (86%)
- INFERRED: 1 (14%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*