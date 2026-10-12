# Status Severity & Exit Codes

> 8 nodes · cohesion 0.32

## Key Concepts

- **severity 数值序（_STATUS_SEVERITY）** (4 connections) — `docs/adr/0031-job-lifecycle-states-and-severity.md`
- **_NON_VERDICT 与 _aggregate 入口过滤** (3 connections) — `docs/adr/0031-job-lifecycle-states-and-severity.md`
- **Status.SKIPPED（core 派生态）** (3 connections) — `docs/adr/0031-job-lifecycle-states-and-severity.md`
- **step 级短路：step_skipped 事件 + shortcircuited 布尔** (3 connections) — `docs/adr/0031-job-lifecycle-states-and-severity.md`
- **退出码基于 run 级 severity** (2 connections) — `docs/adr/0031-job-lifecycle-states-and-severity.md`
- **Status.ABORTED（core 派生态）** (2 connections) — `docs/adr/0031-job-lifecycle-states-and-severity.md`
- **Status.PENDING / RUNNING（生命周期前置态）** (2 connections) — `docs/adr/0031-job-lifecycle-states-and-severity.md`
- **TERMINAL_STATUSES（终态真源，取补定义）** (2 connections) — `docs/adr/0031-job-lifecycle-states-and-severity.md`

## Relationships

- [Execution Architecture ADRs](Execution_Architecture_ADRs.md) (2 shared connections)
- [Contributor Docs And ADRs](Contributor_Docs_And_ADRs.md) (1 shared connections)

## Source Files

- `docs/adr/0031-job-lifecycle-states-and-severity.md`

## Audit Trail

- EXTRACTED: 12 (100%)
- INFERRED: 0 (0%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*