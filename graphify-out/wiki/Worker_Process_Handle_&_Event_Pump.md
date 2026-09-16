# Worker Process Handle & Event Pump

> 16 nodes · cohesion 0.15

## Key Concepts

- **_read_events()** (8 connections) — `core/gherkai_core/adapters/subprocess_engine.py`
- **.run_scope()** (7 connections) — `core/gherkai_core/adapters/subprocess_engine.py`
- **SubprocessWorkerHandle** (7 connections) — `core/gherkai_core/adapters/subprocess_engine.py`
- **_join_pumps()** (4 connections) — `core/gherkai_core/adapters/subprocess_engine.py`
- **_pump_log()** (3 connections) — `core/gherkai_core/adapters/subprocess_engine.py`
- **Event** (2 connections)
- **Popen** (2 connections)
- **.__init__()** (2 connections) — `core/gherkai_core/adapters/subprocess_engine.py`
- **.stop()** (2 connections) — `core/gherkai_core/adapters/subprocess_engine.py`
- **.wait()** (2 connections) — `core/gherkai_core/adapters/subprocess_engine.py`
- **Job** (1 connections)
- **有界等 worker 日志 pump 线程结束（进程退了它们读到 EOF 就完）。超时不等——孙进程可能仍持写端。** (1 connections) — `core/gherkai_core/adapters/subprocess_engine.py`
- **逐行读 fd3（纯 ADR 0024 事件）→ Event。worker 异常退出且 returncode>0 时抛错（schedule 记 error）。…** (1 connections) — `core/gherkai_core/adapters/subprocess_engine.py`
- **把 worker 的 stdout（SDK 噪声，tag=out）/ stderr（诊断，tag=err）实时透传为本进程日志。 带 [worker…** (1 connections) — `core/gherkai_core/adapters/subprocess_engine.py`
- **一个在跑的 worker 子进程的句柄。stop() 翻成 SIGTERM→宽限→SIGKILL（ADR 0026 机制层）。** (1 connections) — `core/gherkai_core/adapters/subprocess_engine.py`
- **阻塞等 worker 退出、返回 returncode（ADR 0034：local 无状态跑批的退出观察者用）。 per-run 进程的…** (1 connections) — `core/gherkai_core/adapters/subprocess_engine.py`

## Relationships

- [SQLite Event Log](SQLite_Event_Log.md) (5 shared connections)
- [Cloud Boto3 Guards & EventLog](Cloud_Boto3_Guards_%26_EventLog.md) (3 shared connections)
- [Job Explain & S3 Offload](Job_Explain_%26_S3_Offload.md) (1 shared connections)

## Source Files

- `core/gherkai_core/adapters/subprocess_engine.py`

## Audit Trail

- EXTRACTED: 25 (93%)
- INFERRED: 2 (7%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*