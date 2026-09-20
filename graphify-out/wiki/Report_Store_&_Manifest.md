# Report Store & Manifest

> 6 nodes · cohesion 0.40

## Key Concepts

- **ADR 0034: 无状态批量运行（CQRS + reconciler）** (8 connections) — `docs/adr/0034-detached-batch-reconciler.md`
- **ReportStore.write(run_id, result)** (5 connections) — `docs/adr/0027-runreport-aggregation-index.md`
- **commit point 写序（数据面先、控制面后）** (3 connections) — `docs/adr/0030-realtime-persistence-seam.md`
- **manifest.json（薄信封 + 扁平 report_index）** (2 connections) — `docs/adr/0027-runreport-aggregation-index.md`
- **href 相对化（local 相对 / cloud 恒等 ref）** (1 connections) — `docs/adr/0027-runreport-aggregation-index.md`
- **run_id（归集主键，生成权在组合根）** (1 connections) — `docs/adr/0027-runreport-aggregation-index.md`

## Relationships

- [Schedule & Retry ADRs](Schedule_%26_Retry_ADRs.md) (2 shared connections)
- [Report Aggregation & Status](Report_Aggregation_%26_Status.md) (2 shared connections)
- [Artifact Upload & Shutdown](Artifact_Upload_%26_Shutdown.md) (1 shared connections)
- [Run Persistence & Preflight](Run_Persistence_%26_Preflight.md) (1 shared connections)
- [DynamoDB Storage Design](DynamoDB_Storage_Design.md) (1 shared connections)
- [Detached Run Orchestration](Detached_Run_Orchestration.md) (1 shared connections)

## Source Files

- `docs/adr/0027-runreport-aggregation-index.md`
- `docs/adr/0030-realtime-persistence-seam.md`
- `docs/adr/0034-detached-batch-reconciler.md`

## Audit Trail

- EXTRACTED: 14 (100%)
- INFERRED: 0 (0%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*