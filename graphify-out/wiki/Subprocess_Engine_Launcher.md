# Subprocess Engine Launcher

> 12 nodes · cohesion 0.18

## Key Concepts

- **SubprocessEngine** (21 connections) — `core/gherkai_core/adapters/subprocess_engine.py`
- **SubprocessLauncher** (17 connections) — `runtime/gherkai_runtime/detached.py`
- **._pump()** (4 connections) — `runtime/gherkai_runtime/detached.py`
- **.__init__()** (3 connections) — `runtime/gherkai_runtime/detached.py`
- **.launch()** (2 connections) — `runtime/gherkai_runtime/detached.py`
- **Engine port 的子进程实现。cmd 是启 worker 的命令行（如 ['uv','run','python','run_scope.py']）。** (1 connections) — `core/gherkai_core/adapters/subprocess_engine.py`
- **.__init__()** (1 connections) — `core/gherkai_core/adapters/subprocess_engine.py`
- **Event** (1 connections)
- **Job** (1 connections)
- **驱动一个 worker 的 fd3 事件流直到结束（落库在 raw_sink 里做）；结束后 handle.wait() 拿 exitcode 写…** (1 connections) — `runtime/gherkai_runtime/detached.py`
- **local Launcher（ADR 0034 机制四回调 + 机制二退出观察者）。 launch(job)：起 worker（resolver 按…** (1 connections) — `runtime/gherkai_runtime/detached.py`
- **Timer** (1 connections)

## Relationships

- [Detached Launcher Tests](Detached_Launcher_Tests.md) (5 shared connections)
- [Run Metadata & S3 Offload](Run_Metadata_%26_S3_Offload.md) (4 shared connections)
- [Subprocess Engine Tests](Subprocess_Engine_Tests.md) (3 shared connections)
- [S3 Report Store](S3_Report_Store.md) (3 shared connections)
- [Local Reconcile Rebuild](Local_Reconcile_Rebuild.md) (2 shared connections)
- [Subprocess Engine Adapter](Subprocess_Engine_Adapter.md) (2 shared connections)
- [SSM Paths & Composition Root](SSM_Paths_%26_Composition_Root.md) (2 shared connections)
- [Timestamps & Wallclock](Timestamps_%26_Wallclock.md) (2 shared connections)
- [Submit & Tunnel CLI Wiring](Submit_%26_Tunnel_CLI_Wiring.md) (1 shared connections)
- [Unavailable Engine Placeholder](Unavailable_Engine_Placeholder.md) (1 shared connections)
- [Worker Capability Query](Worker_Capability_Query.md) (1 shared connections)
- [Local Detached Execution](Local_Detached_Execution.md) (1 shared connections)

## Source Files

- `core/gherkai_core/adapters/subprocess_engine.py`
- `runtime/gherkai_runtime/detached.py`

## Audit Trail

- EXTRACTED: 29 (69%)
- INFERRED: 13 (31%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*