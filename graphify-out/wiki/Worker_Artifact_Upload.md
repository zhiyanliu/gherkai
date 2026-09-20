# Worker Artifact Upload

> 4 nodes · cohesion 0.50

## Key Concepts

- **artifact_upload.py** (6 connections) — `engines/novaact/gherkai_worker_novaact/lib/artifact_upload.py`
- **_log()** (3 connections) — `engines/novaact/gherkai_worker_novaact/lib/artifact_upload.py`
- **产物 S3 上传（Nova worker，ADR 0029 第一期）：整目录上传 → 删本地 → reportRef 报 s3://。 由组合根注入的 S3…** (1 connections) — `engines/novaact/gherkai_worker_novaact/lib/artifact_upload.py`
- **诊断走 stderr（与 worker 主流程同一诊断面、与协议事件物理隔离，ADR 0024 三通道分离）。 本模块**不 import run_scope…** (1 connections) — `engines/novaact/gherkai_worker_novaact/lib/artifact_upload.py`

## Relationships

- [Python Artifact Uploader](Python_Artifact_Uploader.md) (3 shared connections)
- [Nova Act Worker Entry](Nova_Act_Worker_Entry.md) (1 shared connections)
- [Artifact Upload Tests](Artifact_Upload_Tests.md) (1 shared connections)

## Source Files

- `engines/novaact/gherkai_worker_novaact/lib/artifact_upload.py`

## Audit Trail

- EXTRACTED: 8 (100%)
- INFERRED: 0 (0%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*