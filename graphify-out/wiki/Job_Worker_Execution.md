# Job Worker Execution

> 16 nodes · cohesion 0.17

## Key Concepts

- **_Worker** (21 connections) — `core/gherkai_core/schedule.py`
- **._run_once()** (9 connections) — `core/gherkai_core/schedule.py`
- **.__init__()** (7 connections) — `core/gherkai_core/schedule.py`
- **._reduce()** (6 connections) — `core/gherkai_core/schedule.py`
- **.run()** (4 connections) — `core/gherkai_core/schedule.py`
- **_heartbeat_wrap()** (3 connections) — `core/gherkai_core/schedule.py`
- **Event** (3 connections)
- **._emit()** (3 connections) — `core/gherkai_core/schedule.py`
- **._stop()** (2 connections) — `core/gherkai_core/schedule.py`
- **Sink** (2 connections)
- **Job** (1 connections)
- **单个 job 的执行体：在线程里运行，迭代事件流、转 sink、归约成 JobResult。** (1 connections) — `core/gherkai_core/schedule.py`
- **运行一个 job，含网络瞬时故障的选择性重试（ADR 0028）。 重试门槛（双条件 AND，绝不放宽）：① 本次以 network_error…** (1 connections) — `core/gherkai_core/schedule.py`
- **单次执行 job。返回 (JobResult, 是否 network_error, 是否 emit 过 step_done)。 deadline：run…** (1 connections) — `core/gherkai_core/schedule.py`
- **把 adapter 的纯 `Iterator[Event]` 包成「事件 + 静默心跳」流（ADR 0026/0028）。 单线程无法在…** (1 connections) — `core/gherkai_core/schedule.py`
- **Lock** (1 connections)

## Relationships

- [Run Result Aggregation Tree](Run_Result_Aggregation_Tree.md) (11 shared connections)
- [Event Log Adapters](Event_Log_Adapters.md) (5 shared connections)
- [Run Scheduling Core](Run_Scheduling_Core.md) (3 shared connections)
- [Job Domain Models](Job_Domain_Models.md) (2 shared connections)
- [Event Formatting](Event_Formatting.md) (1 shared connections)
- [Typed Errors and Wire Protocol](Typed_Errors_and_Wire_Protocol.md) (1 shared connections)
- [Job Status Severity Aggregation](Job_Status_Severity_Aggregation.md) (1 shared connections)

## Source Files

- `core/gherkai_core/schedule.py`

## Audit Trail

- EXTRACTED: 33 (73%)
- INFERRED: 12 (27%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*