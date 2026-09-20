# Fake S3 Client

> 5 nodes · cohesion 0.40

## Key Concepts

- **_FakeS3** (11 connections) — `cli/tests/test_backend_cloud.py`
- **.head_bucket()** (1 connections) — `cli/tests/test_backend_cloud.py`
- **.__init__()** (1 connections) — `cli/tests/test_backend_cloud.py`
- **.put_object()** (1 connections) — `cli/tests/test_backend_cloud.py`
- **假 S3 client：三个件套共享一个；记录 head_bucket（begin 探活）/put_object。** (1 connections) — `cli/tests/test_backend_cloud.py`

## Relationships

- [Cloud Backend CLI Tests](Cloud_Backend_CLI_Tests.md) (2 shared connections)
- [S3 Result Store Port](S3_Result_Store_Port.md) (1 shared connections)
- [Explain Rendering Tests](Explain_Rendering_Tests.md) (1 shared connections)
- [Event Log & Projection](Event_Log_%26_Projection.md) (1 shared connections)
- [Run State Rendering](Run_State_Rendering.md) (1 shared connections)
- [SSM Paths & Composition Root](SSM_Paths_%26_Composition_Root.md) (1 shared connections)

## Source Files

- `cli/tests/test_backend_cloud.py`

## Audit Trail

- EXTRACTED: 6 (55%)
- INFERRED: 5 (45%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*