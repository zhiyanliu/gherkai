# Fake DynamoDB Table

> 7 nodes · cohesion 0.29

## Key Concepts

- **_FakeTable** (8 connections) — `cli/tests/test_backend_cloud.py`
- **.get_item()** (1 connections) — `cli/tests/test_backend_cloud.py`
- **.__init__()** (1 connections) — `cli/tests/test_backend_cloud.py`
- **.load()** (1 connections) — `cli/tests/test_backend_cloud.py`
- **.put_item()** (1 connections) — `cli/tests/test_backend_cloud.py`
- **.update_item()** (1 connections) — `cli/tests/test_backend_cloud.py`
- **假 DDB table 句柄：DynamoDBRunStore…** (1 connections) — `cli/tests/test_backend_cloud.py`

## Relationships

- [Cloud Backend CLI Tests](Cloud_Backend_CLI_Tests.md) (1 shared connections)
- [Cloud Composition Helpers](Cloud_Composition_Helpers.md) (1 shared connections)

## Source Files

- `cli/tests/test_backend_cloud.py`

## Audit Trail

- EXTRACTED: 7 (88%)
- INFERRED: 1 (12%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*