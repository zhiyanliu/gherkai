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

- [Run Result Rendering](Run_Result_Rendering.md) (2 shared connections)
- [Cloud Backend CLI Tests](Cloud_Backend_CLI_Tests.md) (1 shared connections)
- [State Projection & Planning](State_Projection_%26_Planning.md) (1 shared connections)
- [Boto Guard & S3 Offload](Boto_Guard_%26_S3_Offload.md) (1 shared connections)
- [SSM Path & Client Composition](SSM_Path_%26_Client_Composition.md) (1 shared connections)

## Source Files

- `cli/tests/test_backend_cloud.py`

## Audit Trail

- EXTRACTED: 7 (58%)
- INFERRED: 5 (42%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*