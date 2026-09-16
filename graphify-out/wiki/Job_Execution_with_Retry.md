# Job Execution with Retry

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
- **单个 job 的执行体：跑在线程里，迭代事件流、转 sink、归约成 JobResult。** (1 connections) — `core/gherkai_core/schedule.py`
- **跑一个 job，含网络瞬时故障的选择性重试（ADR 0028）。 重试门槛（双条件 AND，绝不放宽）：① 本次以 network_error…** (1 connections) — `core/gherkai_core/schedule.py`
- **单次执行 job。返回 (JobResult, 是否 network_error, 是否 emit 过 step_done)。 deadline：run…** (1 connections) — `core/gherkai_core/schedule.py`
- **把 adapter 的纯 `Iterator[Event]` 包成「事件 + 静默心跳」流（ADR 0026/0028）。 单线程无法在…** (1 connections) — `core/gherkai_core/schedule.py`
- **Lock** (1 connections)

## Relationships

- [Cloud Boto3 Guards & EventLog](Cloud_Boto3_Guards_%26_EventLog.md) (8 shared connections)
- [S3 Result Store](S3_Result_Store.md) (4 shared connections)
- [Event Formatting](Event_Formatting.md) (4 shared connections)
- [Schedule Core & Fakes](Schedule_Core_%26_Fakes.md) (3 shared connections)
- [Job Explain & S3 Offload](Job_Explain_%26_S3_Offload.md) (2 shared connections)
- [Typed Errors & Severity](Typed_Errors_%26_Severity.md) (2 shared connections)
- [Text Render & Wording Guards](Text_Render_%26_Wording_Guards.md) (1 shared connections)

## Source Files

- `core/gherkai_core/schedule.py`

## Audit Trail

- EXTRACTED: 33 (73%)
- INFERRED: 12 (27%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*