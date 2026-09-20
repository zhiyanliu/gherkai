# Log Upload Enablement

> 2 nodes · cohesion 1.00

## Key Concepts

- **.enabled()** (2 connections) — `engines/novaact/gherkai_worker_novaact/lib/artifact_upload.py`
- **是否上传（注入了桶 + 有 run_dir 算相对 key）。否则 no-op 报 file://。** (1 connections) — `engines/novaact/gherkai_worker_novaact/lib/artifact_upload.py`

## Relationships

- [Python Artifact Uploader](Python_Artifact_Uploader.md) (1 shared connections)

## Source Files

- `engines/novaact/gherkai_worker_novaact/lib/artifact_upload.py`

## Audit Trail

- EXTRACTED: 2 (100%)
- INFERRED: 0 (0%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*