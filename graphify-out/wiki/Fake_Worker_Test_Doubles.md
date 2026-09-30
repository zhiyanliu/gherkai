# Fake Worker Test Doubles

> 16 nodes · cohesion 0.18

## Key Concepts

- **_NetRaiseEngine** (20 connections) — `core/tests/test_lifecycle_states.py`
- **FakeWorkerHandle** (12 connections) — `core/tests/fake_engine.py`
- **._gen()** (6 connections) — `core/tests/fake_engine.py`
- **.run_scope()** (5 connections) — `core/tests/fake_engine.py`
- **._gen()** (5 connections) — `core/tests/test_lifecycle_states.py`
- **Event** (4 connections)
- **.__init__()** (3 connections) — `core/tests/fake_engine.py`
- **Job** (3 connections)
- **.run_scope()** (3 connections) — `core/tests/test_lifecycle_states.py`
- **.run_scope()** (3 connections) — `core/tests/test_lifecycle_states.py`
- **.__call__()** (2 connections) — `core/tests/fake_engine.py`
- **.__init__()** (2 connections) — `core/tests/test_lifecycle_states.py`
- **.__init__()** (1 connections) — `core/tests/fake_engine.py`
- **.stop()** (1 connections) — `core/tests/fake_engine.py`
- **Event** (1 connections)
- **victim job 的 worker：等一个 gate 放行后才抛 WorkerNetworkError（模拟「建连退避期间」被中止/超时后以退出码 80…** (1 connections) — `core/tests/test_lifecycle_states.py`

## Relationships

- [Run Scheduling Core](Run_Scheduling_Core.md) (10 shared connections)
- [Typed Errors and Wire Protocol](Typed_Errors_and_Wire_Protocol.md) (5 shared connections)
- [Event Formatting](Event_Formatting.md) (5 shared connections)
- [Job Status Severity Aggregation](Job_Status_Severity_Aggregation.md) (2 shared connections)
- [Job Domain Models](Job_Domain_Models.md) (2 shared connections)
- [Run Result Aggregation Tree](Run_Result_Aggregation_Tree.md) (2 shared connections)
- [Run State Projection](Run_State_Projection.md) (2 shared connections)

## Source Files

- `core/tests/fake_engine.py`
- `core/tests/test_lifecycle_states.py`

## Audit Trail

- EXTRACTED: 34 (68%)
- INFERRED: 16 (32%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*