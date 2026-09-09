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

- [Run Result Verdict Model](Run_Result_Verdict_Model.md) (3 shared connections)
- [Cloud Backend CLI Tests](Cloud_Backend_CLI_Tests.md) (1 shared connections)
- [SQLite Event Log & Projection](SQLite_Event_Log_%26_Projection.md) (1 shared connections)
- [Composition Root Wiring](Composition_Root_Wiring.md) (1 shared connections)

## Source Files

- `cli/tests/test_backend_cloud.py`

## Audit Trail

- EXTRACTED: 7 (58%)
- INFERRED: 5 (42%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*