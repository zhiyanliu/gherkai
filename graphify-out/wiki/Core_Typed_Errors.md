# Core Typed Errors

> 35 nodes · cohesion 0.09

## Key Concepts

- **test_lifecycle_states.py** (46 connections) — `core/tests/test_lifecycle_states.py`
- **WorkerNetworkError** (26 connections) — `core/gherkai_core/errors.py`
- **_NetRaiseEngine** (20 connections) — `core/tests/test_lifecycle_states.py`
- **fake_engine.py** (12 connections) — `core/tests/fake_engine.py`
- **FakeWorkerHandle** (12 connections) — `core/tests/fake_engine.py`
- **errors.py** (10 connections) — `core/gherkai_core/errors.py`
- **severity()** (7 connections) — `core/gherkai_core/model.py`
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
- **test_pending_running_have_no_severity()** (2 connections) — `core/tests/test_lifecycle_states.py`
- **test_severity_full_chain()** (2 connections) — `core/tests/test_lifecycle_states.py`
- **test_severity_order_fixes_string_sort_trap()** (2 connections) — `core/tests/test_lifecycle_states.py`
- **RuntimeError** (1 connections)
- **core 的类型化异常（ADR 0028）。 放 core 而非 adapter：schedule 要 catch 它做 network 重试判定，若定义在…** (1 connections) — `core/gherkai_core/errors.py`
- **worker 以「网络/SSL 瞬时故障」专用退出码退出（建连失败、重试耗尽，ADR 0028）。 `wire.raise_for_worker_exit`…** (1 connections) — `core/gherkai_core/errors.py`
- **终态的 severity 数值（ADR 0031）。前置态 pending/running 无 severity，调用即编程错误。** (1 connections) — `core/gherkai_core/model.py`
- **.__init__()** (1 connections) — `core/tests/fake_engine.py`
- *... and 10 more nodes in this community*

## Relationships

- [Run Scheduling Core](Run_Scheduling_Core.md) (31 shared connections)
- [Event Progress Formatting](Event_Progress_Formatting.md) (13 shared connections)
- [S3 Result Store Port](S3_Result_Store_Port.md) (7 shared connections)
- [Run State Rendering](Run_State_Rendering.md) (6 shared connections)
- [Event Log & Projection](Event_Log_%26_Projection.md) (6 shared connections)
- [Run Metadata & S3 Offload](Run_Metadata_%26_S3_Offload.md) (4 shared connections)
- [Local & S3 Result Stores](Local_%26_S3_Result_Stores.md) (4 shared connections)
- [Scope Tag Resolution](Scope_Tag_Resolution.md) (2 shared connections)
- [Fargate Engine Tests](Fargate_Engine_Tests.md) (2 shared connections)
- [Wire Protocol Serialization](Wire_Protocol_Serialization.md) (2 shared connections)
- [Subprocess Engine Tests](Subprocess_Engine_Tests.md) (2 shared connections)
- [Fargate Event Read Tests](Fargate_Event_Read_Tests.md) (2 shared connections)

## Source Files

- `core/gherkai_core/errors.py`
- `core/gherkai_core/model.py`
- `core/tests/fake_engine.py`
- `core/tests/test_lifecycle_states.py`

## Audit Trail

- EXTRACTED: 110 (80%)
- INFERRED: 27 (20%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*