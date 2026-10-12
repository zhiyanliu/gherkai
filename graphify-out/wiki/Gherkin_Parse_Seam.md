# Gherkin Parse Seam

> 4 nodes · cohesion 0.50

## Key Concepts

- **parse seam（藏 gherkin-official）** (4 connections) — `docs/adr/0025-plan-module-feature-to-jobs.md`
- **step 顺序 = 书写顺序，keyword 只决定派发** (2 connections) — `docs/adr/0025-plan-module-feature-to-jobs.md`
- **gherkin-official 第三方库 seam** (1 connections) — `docs/adr/0025-plan-module-feature-to-jobs.md`
- **keyword 判不出 → fail-fast（PlanError）** (1 connections) — `docs/adr/0025-plan-module-feature-to-jobs.md`

## Relationships

- [Engine Port And Job Plan](Engine_Port_And_Job_Plan.md) (1 shared connections)
- [Worker Termination Contract](Worker_Termination_Contract.md) (1 shared connections)

## Source Files

- `docs/adr/0025-plan-module-feature-to-jobs.md`

## Audit Trail

- EXTRACTED: 4 (80%)
- INFERRED: 0 (0%)
- AMBIGUOUS: 1 (20%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*