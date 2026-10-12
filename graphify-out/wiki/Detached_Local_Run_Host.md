# Detached Local Run Host

> 14 nodes · cohesion 0.15

## Key Concepts

- **detached.py** (20 connections) — `runtime/gherkai_runtime/detached.py`
- **event_log/__init__.py** (11 connections) — `core/gherkai_core/adapters/event_log/__init__.py`
- **drive_local_reconcile()** (6 connections) — `runtime/gherkai_runtime/detached.py`
- **test_drive_local_reconcile_drives_to_terminal_then_tears_down_tunnel()** (6 connections) — `runtime/tests/test_detached_launcher.py`
- **cleanup_tunnel()** (4 connections) — `runtime/gherkai_runtime/detached.py`
- **_paths()** (3 connections) — `runtime/gherkai_runtime/detached.py`
- **write_tunnel_file()** (3 connections) — `runtime/gherkai_runtime/detached.py`
- **events 日志 adapter（ADR 0034）：持久事件通道，reconciler 从此全量重放推演 RunState。…** (1 connections) — `core/gherkai_core/adapters/event_log/__init__.py`
- **无状态批量运行的 local 执行接线（ADR 0034，本机后端）：SubprocessLauncher + per-run reconciler 进程。…** (1 connections) — `runtime/gherkai_runtime/detached.py`
- **local 推进的**唯一入口**（ADR 0034 三宿主同一套机制）：装配 → tick 到终态 → 拆隧道。per-run 进程与 `status…** (1 connections) — `runtime/gherkai_runtime/detached.py`
- **local 无状态批量运行的落点：events SQLite 与 RunStore/ResultStore 同在 <report_dir>/<run_id>/。** (1 connections) — `runtime/gherkai_runtime/detached.py`
- **local submit 落隧道收尾凭据：进程对象句柄跨进程传不过去，pid 落盘是唯一通道（ADR 0035）。** (1 connections) — `runtime/gherkai_runtime/detached.py`
- **收尾者（per-run 终态后 / status --wait 接力后）拆隧道：有 tunnel.json 才动作，幂等。** (1 connections) — `runtime/gherkai_runtime/detached.py`
- **local 推进唯一入口的三步护栏（ADR 0034 三宿主同一套机制 + ADR 0035「终态即拆」）：装配 → 推到终态 → 拆隧道。 只把引擎替成…** (1 connections) — `runtime/tests/test_detached_launcher.py`

## Relationships

- [Detached Launcher Reconcile Loop](Detached_Launcher_Reconcile_Loop.md) (5 shared connections)
- [Cloud Adapter Boundary Modules](Cloud_Adapter_Boundary_Modules.md) (4 shared connections)
- [Local Reconcile Rebuild](Local_Reconcile_Rebuild.md) (4 shared connections)
- [Cloud Launcher Reconcile Tests](Cloud_Launcher_Reconcile_Tests.md) (2 shared connections)
- [Ngrok Tunnel Provider](Ngrok_Tunnel_Provider.md) (2 shared connections)
- [Run State Store](Run_State_Store.md) (2 shared connections)
- [SSM Paths And Compose](SSM_Paths_And_Compose.md) (2 shared connections)
- [Subprocess Engine & Launcher](Subprocess_Engine_%26_Launcher.md) (2 shared connections)
- [SQLite Event Log](SQLite_Event_Log.md) (1 shared connections)
- [EventLog And Launcher Ports](EventLog_And_Launcher_Ports.md) (1 shared connections)
- [SQLite Event Log Tests](SQLite_Event_Log_Tests.md) (1 shared connections)
- [Lambda Handler Event Parsing Tests](Lambda_Handler_Event_Parsing_Tests.md) (1 shared connections)

## Source Files

- `core/gherkai_core/adapters/event_log/__init__.py`
- `runtime/gherkai_runtime/detached.py`
- `runtime/tests/test_detached_launcher.py`

## Audit Trail

- EXTRACTED: 45 (98%)
- INFERRED: 1 (2%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*