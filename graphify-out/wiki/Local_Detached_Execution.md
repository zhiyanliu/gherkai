# Local Detached Execution

> 8 nodes · cohesion 0.29

## Key Concepts

- **detached.py** (19 connections) — `runtime/gherkai_runtime/detached.py`
- **drive_local_reconcile()** (6 connections) — `runtime/gherkai_runtime/detached.py`
- **cleanup_tunnel()** (4 connections) — `runtime/gherkai_runtime/detached.py`
- **write_tunnel_file()** (3 connections) — `runtime/gherkai_runtime/detached.py`
- **无状态批量运行的 local 执行接线（ADR 0034，本机后端）：SubprocessLauncher + per-run reconciler 进程。…** (1 connections) — `runtime/gherkai_runtime/detached.py`
- **local 推进的**唯一入口**（ADR 0034 三宿主同一套机制）：装配 → tick 到终态 → 拆隧道。per-run 进程与 `status…** (1 connections) — `runtime/gherkai_runtime/detached.py`
- **local submit 落隧道收尾凭据：进程对象句柄跨进程传不过去，pid 落盘是唯一通道（ADR 0035）。** (1 connections) — `runtime/gherkai_runtime/detached.py`
- **收尾者（per-run 终态后 / status --wait 接力后）拆隧道：有 tunnel.json 才动作，幂等。** (1 connections) — `runtime/gherkai_runtime/detached.py`

## Relationships

- [Local Reconcile Rebuild](Local_Reconcile_Rebuild.md) (4 shared connections)
- [Detached Launcher Tests](Detached_Launcher_Tests.md) (3 shared connections)
- [Tunnel Provider](Tunnel_Provider.md) (2 shared connections)
- [Run State Rendering](Run_State_Rendering.md) (2 shared connections)
- [DynamoDB Event Log](DynamoDB_Event_Log.md) (1 shared connections)
- [Subprocess Engine Adapter](Subprocess_Engine_Adapter.md) (1 shared connections)
- [Reconcile Orchestration](Reconcile_Orchestration.md) (1 shared connections)
- [CLI Test Fixtures](CLI_Test_Fixtures.md) (1 shared connections)
- [SSM Paths & Composition Root](SSM_Paths_%26_Composition_Root.md) (1 shared connections)
- [Resource Naming Source](Resource_Naming_Source.md) (1 shared connections)
- [Timestamps & Wallclock](Timestamps_%26_Wallclock.md) (1 shared connections)
- [Subprocess Engine Launcher](Subprocess_Engine_Launcher.md) (1 shared connections)

## Source Files

- `runtime/gherkai_runtime/detached.py`

## Audit Trail

- EXTRACTED: 27 (96%)
- INFERRED: 1 (4%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*