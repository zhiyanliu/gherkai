# Local Detached Run Wiring

> 6 nodes · cohesion 0.33

## Key Concepts

- **detached.py** (17 connections) — `runtime/gherkai_runtime/detached.py`
- **_paths()** (3 connections) — `runtime/gherkai_runtime/detached.py`
- **write_tunnel_file()** (3 connections) — `runtime/gherkai_runtime/detached.py`
- **无状态跑批的 local 执行接线（ADR 0034，local 档）：SubprocessLauncher + per-run reconciler 进程。…** (1 connections) — `runtime/gherkai_runtime/detached.py`
- **local 无状态跑批的落点：events SQLite 与 RunStore/ResultStore 同在 <report_dir>/<run_id>/。** (1 connections) — `runtime/gherkai_runtime/detached.py`
- **local submit 落隧道收尾凭据：进程对象句柄跨进程传不过去，pid 落盘是唯一通道（ADR 0035）。** (1 connections) — `runtime/gherkai_runtime/detached.py`

## Relationships

- [Detached Launcher Reconcile](Detached_Launcher_Reconcile.md) (3 shared connections)
- [Tunnel Cleanup](Tunnel_Cleanup.md) (2 shared connections)
- [Engine Ports & Adapters](Engine_Ports_%26_Adapters.md) (2 shared connections)
- [Run Result Verdict Model](Run_Result_Verdict_Model.md) (1 shared connections)
- [Cloud Launcher & DDB EventLog](Cloud_Launcher_%26_DDB_EventLog.md) (1 shared connections)
- [Run State Rendering & Boto Guard](Run_State_Rendering_%26_Boto_Guard.md) (1 shared connections)
- [Composition Root Wiring](Composition_Root_Wiring.md) (1 shared connections)
- [Reconcile Loop Integration](Reconcile_Loop_Integration.md) (1 shared connections)
- [Timestamp and Clock Utilities](Timestamp_and_Clock_Utilities.md) (1 shared connections)
- [Subprocess Worker Launcher](Subprocess_Worker_Launcher.md) (1 shared connections)
- [ADR Index & Dev Docs](ADR_Index_%26_Dev_Docs.md) (1 shared connections)
- [CLI Run/Submit Commands](CLI_Run-Submit_Commands.md) (1 shared connections)

## Source Files

- `runtime/gherkai_runtime/detached.py`

## Audit Trail

- EXTRACTED: 20 (95%)
- INFERRED: 1 (5%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*