# Subprocess Engine & Launcher

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

- [Detached Launcher Reconcile Loop](Detached_Launcher_Reconcile_Loop.md) (5 shared connections)
- [Store Port Definitions](Store_Port_Definitions.md) (5 shared connections)
- [Job Explain Data Model](Job_Explain_Data_Model.md) (4 shared connections)
- [Subprocess Engine Tests](Subprocess_Engine_Tests.md) (3 shared connections)
- [Detached Local Run Host](Detached_Local_Run_Host.md) (2 shared connections)
- [Subprocess Engine Adapter](Subprocess_Engine_Adapter.md) (2 shared connections)
- [Timestamp & Wallclock Utils](Timestamp_%26_Wallclock_Utils.md) (2 shared connections)
- [Tunnel CLI Wiring Tests](Tunnel_CLI_Wiring_Tests.md) (1 shared connections)
- [SSM Paths And Compose](SSM_Paths_And_Compose.md) (1 shared connections)
- [Step Argument S3 Offload](Step_Argument_S3_Offload.md) (1 shared connections)
- [Local Reconcile Rebuild](Local_Reconcile_Rebuild.md) (1 shared connections)
- [Cloud Adapter Boundary Modules](Cloud_Adapter_Boundary_Modules.md) (1 shared connections)

## Source Files

- `core/gherkai_core/adapters/subprocess_engine.py`
- `runtime/gherkai_runtime/detached.py`

## Audit Trail

- EXTRACTED: 29 (69%)
- INFERRED: 13 (31%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*