# Artifact Upload Design

> 13 nodes · cohesion 0.23

## Key Concepts

- **Artifact Uploader Component** (7 connections) — `docs/adr/0029-engine-artifacts-to-s3.md`
- **Midscene uploader.snapshotLogs(logDir, seen, budgetMs)** (5 connections) — `docs/adr/0029-engine-artifacts-to-s3.md`
- **uploader.flush_and_cleanup(dir)** (4 connections) — `docs/adr/0029-engine-artifacts-to-s3.md`
- **Midscene uploader.snapshotReport(path)** (4 connections) — `docs/adr/0029-engine-artifacts-to-s3.md`
- **uploader.to_report_ref(path)** (4 connections) — `docs/adr/0029-engine-artifacts-to-s3.md`
- **Act-Boundary Pre-upload** (3 connections) — `docs/adr/0029-engine-artifacts-to-s3.md`
- **Accepted Residual Un-uploaded Artifacts** (3 connections) — `docs/adr/0029-engine-artifacts-to-s3.md`
- **Hybrid Upload Timing (two-level failure semantics)** (3 connections) — `docs/adr/0029-engine-artifacts-to-s3.md`
- **ARTIFACT_S3_BUCKET / ARTIFACT_S3_PREFIX Injection** (2 connections) — `docs/adr/0029-engine-artifacts-to-s3.md`
- **Scenario-Boundary Log Pre-upload (Midscene only)** (2 connections) — `docs/adr/0029-engine-artifacts-to-s3.md`
- **Mandatory Upload Timeouts** (2 connections) — `docs/adr/0029-engine-artifacts-to-s3.md`
- **uploader.from_env()** (1 connections) — `docs/adr/0029-engine-artifacts-to-s3.md`
- **Engine Worker (artifact upload caller)** (1 connections) — `docs/adr/0029-engine-artifacts-to-s3.md`

## Relationships

- [Execution Architecture ADRs](Execution_Architecture_ADRs.md) (3 shared connections)
- [Contributor Docs And ADRs](Contributor_Docs_And_ADRs.md) (1 shared connections)
- [Schedule Governance Knobs](Schedule_Governance_Knobs.md) (1 shared connections)

## Source Files

- `docs/adr/0029-engine-artifacts-to-s3.md`

## Audit Trail

- EXTRACTED: 23 (100%)
- INFERRED: 0 (0%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*