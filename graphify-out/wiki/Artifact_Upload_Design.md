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

- [Core Library Concepts & ADRs](Core_Library_Concepts_%26_ADRs.md) (2 shared connections)
- [Schedule Concurrency & Termination](Schedule_Concurrency_%26_Termination.md) (1 shared connections)
- [Cloud Backend Docs & Diagrams](Cloud_Backend_Docs_%26_Diagrams.md) (1 shared connections)
- [Model Selection ADRs](Model_Selection_ADRs.md) (1 shared connections)

## Source Files

- `docs/adr/0029-engine-artifacts-to-s3.md`

## Audit Trail

- EXTRACTED: 23 (100%)
- INFERRED: 0 (0%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*