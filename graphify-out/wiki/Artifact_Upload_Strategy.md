# Artifact Upload Strategy

> 14 nodes · cohesion 0.22

## Key Concepts

- **ArtifactUploader（产物落点可注入组件）** (11 connections) — `docs/adr/0029-engine-artifacts-to-s3.md`
- **uploader.to_report_ref(path)** (5 connections) — `docs/adr/0029-engine-artifacts-to-s3.md`
- **uploader.flush_and_cleanup(dir)** (4 connections) — `docs/adr/0029-engine-artifacts-to-s3.md`
- **Midscene uploader.snapshotLogs(logDir, seen, budgetMs)** (4 connections) — `docs/adr/0029-engine-artifacts-to-s3.md`
- **Midscene uploader.snapshotReport(path)** (4 connections) — `docs/adr/0029-engine-artifacts-to-s3.md`
- **Hybrid Upload Timing (Realtime reportRef + Scope-End Flush)** (4 connections) — `docs/adr/0029-engine-artifacts-to-s3.md`
- **Act-Boundary Pre-Send (Level 3)** (3 connections) — `docs/adr/0029-engine-artifacts-to-s3.md`
- **Accepted Inherent Residue (Unrescued Artifacts)** (3 connections) — `docs/adr/0029-engine-artifacts-to-s3.md`
- **S3 Landing Env Injection (ARTIFACT_S3_BUCKET / ARTIFACT_S3_PREFIX)** (2 connections) — `docs/adr/0029-engine-artifacts-to-s3.md`
- **uploader.from_env()** (2 connections) — `docs/adr/0029-engine-artifacts-to-s3.md`
- **Nova _presend_act_siblings (name-derived sibling pre-send)** (2 connections) — `docs/adr/0029-engine-artifacts-to-s3.md`
- **Scenario-Boundary Pre-Send of Midscene Logs (Level 4)** (2 connections) — `docs/adr/0029-engine-artifacts-to-s3.md`
- **run_scope.py (Nova scope runner)** (2 connections) — `run_scope.py`
- **Delete Local Only On Full Upload Success** (1 connections) — `docs/adr/0029-engine-artifacts-to-s3.md`

## Relationships

- [Core Protocol Documentation](Core_Protocol_Documentation.md) (5 shared connections)
- [CLI Docs and ADRs](CLI_Docs_and_ADRs.md) (4 shared connections)

## Source Files

- `docs/adr/0029-engine-artifacts-to-s3.md`
- `run_scope.py`

## Audit Trail

- EXTRACTED: 25 (86%)
- INFERRED: 4 (14%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*