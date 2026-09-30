# Cloud Store Wiring

> 8 nodes · cohesion 0.39

## Key Concepts

- **compose.build_cloud_stores** (5 connections) — `docs/adr/0030-realtime-persistence-seam.md`
- **Decision 6: cloud adapter persistence form (DDB/S3)** (5 connections) — `docs/adr/0030-realtime-persistence-seam.md`
- **Decision 7: cli cloud backend wiring, preflight and exit-code layering** (4 connections) — `docs/adr/0030-realtime-persistence-seam.md`
- **DynamoDBRunStore** (3 connections) — `docs/adr/0030-realtime-persistence-seam.md`
- **S3StepArgumentOffloader** (3 connections) — `docs/adr/0030-realtime-persistence-seam.md`
- **S3ReportStore** (2 connections) — `docs/adr/0030-realtime-persistence-seam.md`
- **S3ResultStore** (2 connections) — `docs/adr/0030-realtime-persistence-seam.md`
- **compose.build_local_stores** (1 connections) — `docs/adr/0030-realtime-persistence-seam.md`

## Relationships

- [Core Protocol Documentation](Core_Protocol_Documentation.md) (2 shared connections)
- [CLI Docs and ADRs](CLI_Docs_and_ADRs.md) (1 shared connections)

## Source Files

- `docs/adr/0030-realtime-persistence-seam.md`

## Audit Trail

- EXTRACTED: 14 (100%)
- INFERRED: 0 (0%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*