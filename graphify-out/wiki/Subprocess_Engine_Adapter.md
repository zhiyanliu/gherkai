# Subprocess Engine Adapter

> 18 nodes · cohesion 0.15

## Key Concepts

- **subprocess_engine.py** (16 connections) — `core/gherkai_core/adapters/subprocess_engine.py`
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
- **子进程 Engine adapter（ADR 0026 机制层）：spawn 一个讲 ADR 0024 协议的 worker 子进程。 这是 core…** (1 connections) — `core/gherkai_core/adapters/subprocess_engine.py`
- **有界等 worker 日志 pump 线程结束（进程退了它们读到 EOF 就完）。超时不等——孙进程可能仍持写端。** (1 connections) — `core/gherkai_core/adapters/subprocess_engine.py`
- **逐行读 fd3（纯 ADR 0024 事件）→ Event。worker 异常退出且 returncode>0 时抛错（schedule 记 error）。…** (1 connections) — `core/gherkai_core/adapters/subprocess_engine.py`
- **把 worker 的 stdout（SDK 噪声，tag=out）/ stderr（诊断，tag=err）实时透传为本进程日志。 带 [worker…** (1 connections) — `core/gherkai_core/adapters/subprocess_engine.py`
- **一个正在运行的 worker 子进程的句柄。stop() 翻成 SIGTERM→宽限→SIGKILL（ADR 0026 机制层）。** (1 connections) — `core/gherkai_core/adapters/subprocess_engine.py`
- **阻塞等 worker 退出、返回 returncode（ADR 0034：local 无状态批量运行的退出观察者用）。 per-run 进程的…** (1 connections) — `core/gherkai_core/adapters/subprocess_engine.py`

## Relationships

- [Wire Protocol Serialization](Wire_Protocol_Serialization.md) (4 shared connections)
- [Run Metadata & S3 Offload](Run_Metadata_%26_S3_Offload.md) (2 shared connections)
- [Fargate Engine Adapter](Fargate_Engine_Adapter.md) (2 shared connections)
- [Subprocess Engine Launcher](Subprocess_Engine_Launcher.md) (2 shared connections)
- [Run State Rendering](Run_State_Rendering.md) (1 shared connections)
- [Event Progress Formatting](Event_Progress_Formatting.md) (1 shared connections)
- [Subprocess Engine Tests](Subprocess_Engine_Tests.md) (1 shared connections)
- [SSM Paths & Composition Root](SSM_Paths_%26_Composition_Root.md) (1 shared connections)
- [Local Detached Execution](Local_Detached_Execution.md) (1 shared connections)
- [Detached Launcher Tests](Detached_Launcher_Tests.md) (1 shared connections)

## Source Files

- `core/gherkai_core/adapters/subprocess_engine.py`

## Audit Trail

- EXTRACTED: 37 (95%)
- INFERRED: 2 (5%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*