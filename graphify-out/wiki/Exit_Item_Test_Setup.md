# Exit Item Test Setup

> 2 nodes · cohesion 1.00

## Key Concepts

- **_put_exit_item()** (5 connections) — `core/tests/test_fargate_engine.py`
- **预置一条退出观察者形状的 item——**用真写端 DdbEventLog.record_exit 造**（不手抄形状，写端演进本测试自动跟随）。** (1 connections) — `core/tests/test_fargate_engine.py`

## Relationships

- [Fargate Event Drain & Exit Codes](Fargate_Event_Drain_%26_Exit_Codes.md) (2 shared connections)
- [Cloud Launcher & DDB EventLog](Cloud_Launcher_%26_DDB_EventLog.md) (1 shared connections)
- [Fargate Engine Unit Tests](Fargate_Engine_Unit_Tests.md) (1 shared connections)

## Source Files

- `core/tests/test_fargate_engine.py`

## Audit Trail

- EXTRACTED: 5 (100%)
- INFERRED: 0 (0%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*