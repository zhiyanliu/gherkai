# Local Detached Reconcile

> 12 nodes · cohesion 0.18

## Key Concepts

- **detached.py** (19 connections) — `runtime/gherkai_runtime/detached.py`
- **drive_local_reconcile()** (6 connections) — `runtime/gherkai_runtime/detached.py`
- **test_drive_local_reconcile_drives_to_terminal_then_tears_down_tunnel()** (6 connections) — `runtime/tests/test_detached_launcher.py`
- **cleanup_tunnel()** (4 connections) — `runtime/gherkai_runtime/detached.py`
- **_paths()** (3 connections) — `runtime/gherkai_runtime/detached.py`
- **write_tunnel_file()** (3 connections) — `runtime/gherkai_runtime/detached.py`
- **无状态批量运行的 local 执行接线（ADR 0034，本机后端）：SubprocessLauncher + per-run reconciler 进程。…** (1 connections) — `runtime/gherkai_runtime/detached.py`
- **local 推进的**唯一入口**（ADR 0034 三宿主同一套机制）：装配 → tick 到终态 → 拆隧道。per-run 进程与 `status…** (1 connections) — `runtime/gherkai_runtime/detached.py`
- **local 无状态批量运行的落点：events SQLite 与 RunStore/ResultStore 同在 <report_dir>/<run_id>/。** (1 connections) — `runtime/gherkai_runtime/detached.py`
- **local submit 落隧道收尾凭据：进程对象句柄跨进程传不过去，pid 落盘是唯一通道（ADR 0035）。** (1 connections) — `runtime/gherkai_runtime/detached.py`
- **收尾者（per-run 终态后 / status --wait 接力后）拆隧道：有 tunnel.json 才动作，幂等。** (1 connections) — `runtime/gherkai_runtime/detached.py`
- **local 推进唯一入口的三步护栏（ADR 0034 三宿主同一套机制 + ADR 0035「终态即拆」）：装配 → 推到终态 → 拆隧道。 只把引擎替成…** (1 connections) — `runtime/tests/test_detached_launcher.py`

## Relationships

- [Detached Reconcile Loop Tests](Detached_Reconcile_Loop_Tests.md) (4 shared connections)
- [Local Reconcile Rebuild](Local_Reconcile_Rebuild.md) (4 shared connections)
- [Core Adapters Documentation](Core_Adapters_Documentation.md) (3 shared connections)
- [Tunnel Process Teardown](Tunnel_Process_Teardown.md) (2 shared connections)
- [Run State Rendering](Run_State_Rendering.md) (2 shared connections)
- [SQLite Event Log](SQLite_Event_Log.md) (1 shared connections)
- [Tunnel Host Orchestration](Tunnel_Host_Orchestration.md) (1 shared connections)
- [Cloud Composition Helpers](Cloud_Composition_Helpers.md) (1 shared connections)
- [SSM Path Naming](SSM_Path_Naming.md) (1 shared connections)
- [Run Duration & Claims](Run_Duration_%26_Claims.md) (1 shared connections)
- [Subprocess Launcher](Subprocess_Launcher.md) (1 shared connections)
- [CLI Command Entrypoints](CLI_Command_Entrypoints.md) (1 shared connections)

## Source Files

- `runtime/gherkai_runtime/detached.py`
- `runtime/tests/test_detached_launcher.py`

## Audit Trail

- EXTRACTED: 34 (97%)
- INFERRED: 1 (3%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*