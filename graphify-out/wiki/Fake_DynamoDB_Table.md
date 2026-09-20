# Fake DynamoDB Table

> 7 nodes · cohesion 0.29

## Key Concepts

- **_FakeTable** (12 connections) — `cli/tests/test_backend_cloud.py`
- **.get_item()** (1 connections) — `cli/tests/test_backend_cloud.py`
- **.__init__()** (1 connections) — `cli/tests/test_backend_cloud.py`
- **.load()** (1 connections) — `cli/tests/test_backend_cloud.py`
- **.put_item()** (1 connections) — `cli/tests/test_backend_cloud.py`
- **.update_item()** (1 connections) — `cli/tests/test_backend_cloud.py`
- **假 DDB table 句柄：DynamoDBRunStore…** (1 connections) — `cli/tests/test_backend_cloud.py`

## Relationships

- [Cloud Backend CLI Tests](Cloud_Backend_CLI_Tests.md) (1 shared connections)
- [S3 Result Store Port](S3_Result_Store_Port.md) (1 shared connections)
- [Explain Rendering Tests](Explain_Rendering_Tests.md) (1 shared connections)
- [Event Log & Projection](Event_Log_%26_Projection.md) (1 shared connections)
- [Run State Rendering](Run_State_Rendering.md) (1 shared connections)
- [SSM Paths & Composition Root](SSM_Paths_%26_Composition_Root.md) (1 shared connections)

## Source Files

- `cli/tests/test_backend_cloud.py`

## Audit Trail

- EXTRACTED: 7 (58%)
- INFERRED: 5 (42%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*