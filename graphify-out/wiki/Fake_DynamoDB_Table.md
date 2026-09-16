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
- [S3 Result Store](S3_Result_Store.md) (1 shared connections)
- [Text Render & Wording Guards](Text_Render_%26_Wording_Guards.md) (1 shared connections)
- [Run State Projection](Run_State_Projection.md) (1 shared connections)
- [Cloud Boto3 Guards & EventLog](Cloud_Boto3_Guards_%26_EventLog.md) (1 shared connections)
- [Runtime Composition Root](Runtime_Composition_Root.md) (1 shared connections)

## Source Files

- `cli/tests/test_backend_cloud.py`

## Audit Trail

- EXTRACTED: 7 (58%)
- INFERRED: 5 (42%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*