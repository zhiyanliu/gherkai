# Report Aggregation & Status

> 9 nodes · cohesion 0.28

## Key Concepts

- **ADR 0031: job 生命周期态 skipped/aborted + severity** (5 connections) — `docs/adr/0031-job-lifecycle-states-and-severity.md`
- **Status enum 扩展（skipped/aborted/pending/running）** (5 connections) — `docs/adr/0031-job-lifecycle-states-and-severity.md`
- **ADR 0027: RunReport 跨引擎归集索引** (4 connections) — `docs/adr/0027-runreport-aggregation-index.md`
- **ADR 0030: 实时写存储接缝** (4 connections) — `docs/adr/0030-realtime-persistence-seam.md`
- **_aggregate 入口过滤 _NON_VERDICT** (3 connections) — `docs/adr/0031-job-lifecycle-states-and-severity.md`
- **scope 内 step 级短路** (2 connections) — `docs/adr/0028-transient-network-ssl-resilience.md`
- **step_skipped 事件 + StepResult.shortcircuited** (2 connections) — `docs/adr/0031-job-lifecycle-states-and-severity.md`
- **severity 数值序** (1 connections) — `docs/adr/0031-job-lifecycle-states-and-severity.md`
- **TERMINAL_STATUSES（终态真源，取补定义）** (1 connections) — `docs/adr/0031-job-lifecycle-states-and-severity.md`

## Relationships

- [Report Store & Manifest](Report_Store_%26_Manifest.md) (2 shared connections)
- [Plan Module Seams](Plan_Module_Seams.md) (1 shared connections)
- [Artifact Upload & Shutdown](Artifact_Upload_%26_Shutdown.md) (1 shared connections)
- [Run Persistence & Preflight](Run_Persistence_%26_Preflight.md) (1 shared connections)
- [Detached Run Orchestration](Detached_Run_Orchestration.md) (1 shared connections)
- [Schedule & Retry ADRs](Schedule_%26_Retry_ADRs.md) (1 shared connections)

## Source Files

- `docs/adr/0027-runreport-aggregation-index.md`
- `docs/adr/0028-transient-network-ssl-resilience.md`
- `docs/adr/0030-realtime-persistence-seam.md`
- `docs/adr/0031-job-lifecycle-states-and-severity.md`

## Audit Trail

- EXTRACTED: 17 (100%)
- INFERRED: 0 (0%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*