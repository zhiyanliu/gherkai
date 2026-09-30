# Verdict Status Aggregation

> 10 nodes · cohesion 0.29

## Key Concepts

- **_STATUS_SEVERITY 数值序** (7 connections) — `docs/internals/verdict-model.md`
- **_NON_VERDICT 入口过滤名单** (4 connections) — `docs/adr/0031-job-lifecycle-states-and-severity.md`
- **退出码基于 run 级 severity** (3 connections) — `docs/adr/0031-job-lifecycle-states-and-severity.md`
- **Status.PENDING / RUNNING (生命周期前置态)** (3 connections) — `docs/adr/0031-job-lifecycle-states-and-severity.md`
- **Status.SKIPPED (core 派生态)** (3 connections) — `docs/adr/0031-job-lifecycle-states-and-severity.md`
- **step_skipped 独立 wire 事件** (3 connections) — `docs/adr/0031-job-lifecycle-states-and-severity.md`
- **TERMINAL_STATUSES (取补定义的终态真源)** (3 connections) — `docs/adr/0031-job-lifecycle-states-and-severity.md`
- **_aggregate (run 级聚合)** (2 connections) — `docs/adr/0031-job-lifecycle-states-and-severity.md`
- **Status.ABORTED (core 派生态)** (2 connections) — `docs/adr/0031-job-lifecycle-states-and-severity.md`
- **StepResult.shortcircuited (正交布尔)** (1 connections) — `docs/adr/0031-job-lifecycle-states-and-severity.md`

## Relationships

- [Package Contributor Docs](Package_Contributor_Docs.md) (3 shared connections)
- [Architecture Diagrams](Architecture_Diagrams.md) (2 shared connections)

## Source Files

- `docs/adr/0031-job-lifecycle-states-and-severity.md`
- `docs/internals/verdict-model.md`

## Audit Trail

- EXTRACTED: 18 (100%)
- INFERRED: 0 (0%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*