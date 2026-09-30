# Artifact Pre-Send Uploads

> 13 nodes · cohesion 0.23

## Key Concepts

- **ArtifactUploader（产物落点可注入组件）** (10 connections) — `docs/adr/0029-engine-artifacts-to-s3.md`
- **uploader.flush_and_cleanup(dir)** (4 connections) — `docs/adr/0029-engine-artifacts-to-s3.md`
- **Midscene uploader.snapshotLogs(logDir, seen, budgetMs)** (4 connections) — `docs/adr/0029-engine-artifacts-to-s3.md`
- **Midscene uploader.snapshotReport(path)** (4 connections) — `docs/adr/0029-engine-artifacts-to-s3.md`
- **uploader.to_report_ref(path)** (4 connections) — `docs/adr/0029-engine-artifacts-to-s3.md`
- **Hybrid Upload Timing (Realtime reportRef + Scope-End Flush)** (4 connections) — `docs/adr/0029-engine-artifacts-to-s3.md`
- **Act-Boundary Pre-Send (Level 3)** (3 connections) — `docs/adr/0029-engine-artifacts-to-s3.md`
- **S3 Landing Env Injection (ARTIFACT_S3_BUCKET / ARTIFACT_S3_PREFIX)** (2 connections) — `docs/adr/0029-engine-artifacts-to-s3.md`
- **uploader.from_env()** (2 connections) — `docs/adr/0029-engine-artifacts-to-s3.md`
- **Accepted Inherent Residue (Unrescued Artifacts)** (2 connections) — `docs/adr/0029-engine-artifacts-to-s3.md`
- **Nova _presend_act_siblings (name-derived sibling pre-send)** (2 connections) — `docs/adr/0029-engine-artifacts-to-s3.md`
- **Scenario-Boundary Pre-Send of Midscene Logs (Level 4)** (2 connections) — `docs/adr/0029-engine-artifacts-to-s3.md`
- **Delete Local Only On Full Upload Success** (1 connections) — `docs/adr/0029-engine-artifacts-to-s3.md`

## Relationships

- [Package Contributor Docs](Package_Contributor_Docs.md) (8 shared connections)

## Source Files

- `docs/adr/0029-engine-artifacts-to-s3.md`

## Audit Trail

- EXTRACTED: 23 (88%)
- INFERRED: 3 (12%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*