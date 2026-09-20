# Background Upload Queue

> 3 nodes · cohesion 0.67

## Key Concepts

- **.enqueue()** (3 connections) — `engines/novaact/gherkai_worker_novaact/lib/artifact_upload.py`
- **._ensure_worker()** (2 connections) — `engines/novaact/gherkai_worker_novaact/lib/artifact_upload.py`
- **把文件交给后台队列顺序上传（**不阻塞调用方**）；no-op 时直接返回。 调用点在 `step_done` **emit 之后**（ADR 0042…** (1 connections) — `engines/novaact/gherkai_worker_novaact/lib/artifact_upload.py`

## Relationships

- [Python Artifact Uploader](Python_Artifact_Uploader.md) (2 shared connections)

## Source Files

- `engines/novaact/gherkai_worker_novaact/lib/artifact_upload.py`

## Audit Trail

- EXTRACTED: 4 (100%)
- INFERRED: 0 (0%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*