# Run Persistence & Preflight

> 5 nodes · cohesion 0.40

## Key Concepts

- **RunPersistence 应用服务（persist.py）** (4 connections) — `docs/adr/0030-realtime-persistence-seam.md`
- **on_job_complete / on_event 回调注入点** (2 connections) — `docs/adr/0030-realtime-persistence-seam.md`
- **Store.preflight() 探活** (2 connections) — `docs/adr/0030-realtime-persistence-seam.md`
- **两层命名（--prefix 批量默认 + 单资源覆盖）** (2 connections) — `docs/adr/0033-iac-aws-backend-and-composition-wiring.md`
- **preflight fail-fast（点名 prefix）** (2 connections) — `docs/adr/0033-iac-aws-backend-and-composition-wiring.md`

## Relationships

- [Schedule & Retry ADRs](Schedule_%26_Retry_ADRs.md) (1 shared connections)
- [Report Store & Manifest](Report_Store_%26_Manifest.md) (1 shared connections)
- [Report Aggregation & Status](Report_Aggregation_%26_Status.md) (1 shared connections)
- [DynamoDB Storage Design](DynamoDB_Storage_Design.md) (1 shared connections)

## Source Files

- `docs/adr/0030-realtime-persistence-seam.md`
- `docs/adr/0033-iac-aws-backend-and-composition-wiring.md`

## Audit Trail

- EXTRACTED: 8 (100%)
- INFERRED: 0 (0%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*