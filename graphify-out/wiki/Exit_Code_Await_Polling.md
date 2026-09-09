# Exit Code Await Polling

> 9 nodes · cohesion 0.28

## Key Concepts

- **_SeqEcs** (15 connections) — `core/tests/test_fargate_engine.py`
- **_await_engine()** (6 connections) — `core/tests/test_fargate_engine.py`
- **_stopped_resp()** (4 connections) — `core/tests/test_fargate_engine.py`
- **test_await_exit_code_null_beyond_grace_settles_as_error()** (3 connections) — `core/tests/test_fargate_engine.py`
- **test_await_exit_code_null_then_nonzero_landed_preserved()** (3 connections) — `core/tests/test_fargate_engine.py`
- **test_await_exit_code_waits_out_null_then_reads_landed_code()** (3 connections) — `core/tests/test_fargate_engine.py`
- **按序返回 describe_tasks 响应的假 ecs（模拟 STOPPED 翻转后 exitCode 落值时序）。** (1 connections) — `core/tests/test_fargate_engine.py`
- **.describe_tasks()** (1 connections) — `core/tests/test_fargate_engine.py`
- **.__init__()** (1 connections) — `core/tests/test_fargate_engine.py`

## Relationships

- [Fargate Engine Tests](Fargate_Engine_Tests.md) (6 shared connections)
- [Engine Ports & Adapters](Engine_Ports_%26_Adapters.md) (3 shared connections)
- [Fargate Engine](Fargate_Engine.md) (2 shared connections)
- [Event Progress Formatting](Event_Progress_Formatting.md) (2 shared connections)
- [Fargate Worker Handle](Fargate_Worker_Handle.md) (1 shared connections)
- [Terminal Status Aggregation](Terminal_Status_Aggregation.md) (1 shared connections)
- [State Projection & Planning](State_Projection_%26_Planning.md) (1 shared connections)
- [Boto Guard & S3 Offload](Boto_Guard_%26_S3_Offload.md) (1 shared connections)

## Source Files

- `core/tests/test_fargate_engine.py`

## Audit Trail

- EXTRACTED: 17 (63%)
- INFERRED: 10 (37%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*