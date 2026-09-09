# Fake S3 Client

> 5 nodes · cohesion 0.40

## Key Concepts

- **_FakeS3** (11 connections) — `cli/tests/test_backend_cloud.py`
- **.head_bucket()** (1 connections) — `cli/tests/test_backend_cloud.py`
- **.__init__()** (1 connections) — `cli/tests/test_backend_cloud.py`
- **.put_object()** (1 connections) — `cli/tests/test_backend_cloud.py`
- **假 S3 client：三个件套共享一个；记录 head_bucket（begin 探活）/put_object。** (1 connections) — `cli/tests/test_backend_cloud.py`

## Relationships

- [Run Result Verdict Model](Run_Result_Verdict_Model.md) (3 shared connections)
- [Cloud Backend CLI Tests](Cloud_Backend_CLI_Tests.md) (2 shared connections)
- [SQLite Event Log & Projection](SQLite_Event_Log_%26_Projection.md) (1 shared connections)
- [Composition Root Wiring](Composition_Root_Wiring.md) (1 shared connections)

## Source Files

- `cli/tests/test_backend_cloud.py`

## Audit Trail

- EXTRACTED: 6 (55%)
- INFERRED: 5 (45%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*