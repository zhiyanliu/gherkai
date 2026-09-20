# Local No-Op Uploader

> 2 nodes · cohesion 1.00

## Key Concepts

- **test_noop_uploader_enqueue_and_drain_are_immediate()** (3 connections) — `engines/novaact/tests/test_artifact_upload.py`
- **本机 no-op 路径：截图就在本地，队列/排空都是直接返回（不起线程、不碰 boto3）。** (1 connections) — `engines/novaact/tests/test_artifact_upload.py`

## Relationships

- [Python Artifact Uploader](Python_Artifact_Uploader.md) (1 shared connections)
- [Artifact Upload Tests](Artifact_Upload_Tests.md) (1 shared connections)

## Source Files

- `engines/novaact/tests/test_artifact_upload.py`

## Audit Trail

- EXTRACTED: 3 (100%)
- INFERRED: 0 (0%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*