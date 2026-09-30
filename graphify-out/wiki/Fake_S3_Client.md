# Fake S3 Client

> 5 nodes · cohesion 0.40

## Key Concepts

- **_FakeS3** (7 connections) — `cli/tests/test_backend_cloud.py`
- **.head_bucket()** (1 connections) — `cli/tests/test_backend_cloud.py`
- **.__init__()** (1 connections) — `cli/tests/test_backend_cloud.py`
- **.put_object()** (1 connections) — `cli/tests/test_backend_cloud.py`
- **假 S3 client：三个件套共享一个；记录 head_bucket（begin 探活）/put_object。** (1 connections) — `cli/tests/test_backend_cloud.py`

## Relationships

- [Cloud Backend CLI Tests](Cloud_Backend_CLI_Tests.md) (2 shared connections)
- [Cloud Composition Helpers](Cloud_Composition_Helpers.md) (1 shared connections)

## Source Files

- `cli/tests/test_backend_cloud.py`

## Audit Trail

- EXTRACTED: 6 (86%)
- INFERRED: 1 (14%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*