# Subprocess Worker Handle

> 14 nodes · cohesion 0.16

## Key Concepts

- **_read_events()** (7 connections) — `core/gherkai_core/adapters/subprocess_engine.py`
- **.run_scope()** (7 connections) — `core/gherkai_core/adapters/subprocess_engine.py`
- **SubprocessWorkerHandle** (7 connections) — `core/gherkai_core/adapters/subprocess_engine.py`
- **_pump_log()** (3 connections) — `core/gherkai_core/adapters/subprocess_engine.py`
- **Event** (2 connections)
- **Popen** (2 connections)
- **.__init__()** (2 connections) — `core/gherkai_core/adapters/subprocess_engine.py`
- **.wait()** (2 connections) — `core/gherkai_core/adapters/subprocess_engine.py`
- **Job** (1 connections)
- **逐行读 fd3（纯 ADR 0024 事件）→ Event。worker 异常退出且 returncode>0 时抛错（schedule 记 error）。…** (1 connections) — `core/gherkai_core/adapters/subprocess_engine.py`
- **把 worker 的 stdout（SDK 噪声，tag=out）/ stderr（诊断，tag=err）实时透传为本进程日志。 带 [worker…** (1 connections) — `core/gherkai_core/adapters/subprocess_engine.py`
- **一个在跑的 worker 子进程的句柄。stop() 翻成 SIGTERM→宽限→SIGKILL（ADR 0026 机制层）。** (1 connections) — `core/gherkai_core/adapters/subprocess_engine.py`
- **阻塞等 worker 退出、返回 returncode（ADR 0034：local 无状态跑批的退出观察者用）。 per-run 进程的…** (1 connections) — `core/gherkai_core/adapters/subprocess_engine.py`
- **.stop()** (1 connections) — `core/gherkai_core/adapters/subprocess_engine.py`

## Relationships

- [Engine Ports & Adapters](Engine_Ports_%26_Adapters.md) (5 shared connections)
- [Worker Exit Code Translation](Worker_Exit_Code_Translation.md) (1 shared connections)
- [Job Serialization & E2E Harness](Job_Serialization_%26_E2E_Harness.md) (1 shared connections)
- [S3 ReportStore & Subprocess Engine](S3_ReportStore_%26_Subprocess_Engine.md) (1 shared connections)

## Source Files

- `core/gherkai_core/adapters/subprocess_engine.py`

## Audit Trail

- EXTRACTED: 21 (91%)
- INFERRED: 2 (9%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*