# Local Detached Execution

> 26 nodes · cohesion 0.10

## Key Concepts

- **build_local_reconcile()** (20 connections) — `runtime/gherkai_runtime/detached.py`
- **detached.py** (19 connections) — `runtime/gherkai_runtime/detached.py`
- **_seed_for_build()** (13 connections) — `runtime/tests/test_detached_launcher.py`
- **drive_local_reconcile()** (6 connections) — `runtime/gherkai_runtime/detached.py`
- **test_drive_local_reconcile_drives_to_terminal_then_tears_down_tunnel()** (6 connections) — `runtime/tests/test_detached_launcher.py`
- **cleanup_tunnel()** (4 connections) — `runtime/gherkai_runtime/detached.py`
- **test_build_local_reconcile_falls_back_to_flag_when_meta_missing()** (4 connections) — `runtime/tests/test_detached_launcher.py`
- **test_build_local_reconcile_goes_through_resolve_aws_identity()** (4 connections) — `runtime/tests/test_detached_launcher.py`
- **test_build_local_reconcile_host_env_steps_dir_does_not_leak()** (4 connections) — `runtime/tests/test_detached_launcher.py`
- **test_build_local_reconcile_no_steps_dir_when_definition_has_none()** (4 connections) — `runtime/tests/test_detached_launcher.py`
- **test_build_local_reconcile_prefers_meta_max_concurrency()** (4 connections) — `runtime/tests/test_detached_launcher.py`
- **_paths()** (3 connections) — `runtime/gherkai_runtime/detached.py`
- **write_tunnel_file()** (3 connections) — `runtime/gherkai_runtime/detached.py`
- **无状态批量运行的 local 执行接线（ADR 0034，本机后端）：SubprocessLauncher + per-run reconciler 进程。…** (1 connections) — `runtime/gherkai_runtime/detached.py`
- **local 推进的**唯一入口**（ADR 0034 三宿主同一套机制）：装配 → tick 到终态 → 拆隧道。per-run 进程与 `status…** (1 connections) — `runtime/gherkai_runtime/detached.py`
- **local 无状态批量运行的落点：events SQLite 与 RunStore/ResultStore 同在 <report_dir>/<run_id>/。** (1 connections) — `runtime/gherkai_runtime/detached.py`
- **从本地落点重建 per-run reconcile 所需的全部（meta 从 RunStore 读回、log/store/launcher 重建）。 per-…** (1 connections) — `runtime/gherkai_runtime/detached.py`
- **local submit 落隧道收尾凭据：进程对象句柄跨进程传不过去，pid 落盘是唯一通道（ADR 0035）。** (1 connections) — `runtime/gherkai_runtime/detached.py`
- **收尾者（per-run 终态后 / status --wait 接力后）拆隧道：有 tunnel.json 才动作，幂等。** (1 connections) — `runtime/gherkai_runtime/detached.py`
- **后台重建端与前台 run 共用**同一个** region/profile 解析实现（ADR 0016 决策 C）：本函数不自写一份。 换掉…** (1 connections) — `runtime/tests/test_detached_launcher.py`
- **落一个最小 run（单 pending job）供 build_local_reconcile 读回，meta 的 max_concurrency 按参数。** (1 connections) — `runtime/tests/test_detached_launcher.py`
- **并发上限以 definition 为准（ADR 0034 机制四）：入参 flag 与 meta 冲突时用 meta——`status --wait` 接力者…** (1 connections) — `runtime/tests/test_detached_launcher.py`
- **对偶（防「恒取入参」的假绿反面）：meta 无值（打通前落的旧 definition）→ 回落入参 flag。** (1 connections) — `runtime/tests/test_detached_launcher.py`
- **对偶（防「恒注入」假绿）：definition 无 steps_dir（未给/旧落盘/云端后端）→ 宿主不注入该 env， 即便宿主 CWD 下恰好有个…** (1 connections) — `runtime/tests/test_detached_launcher.py`
- **接力者 shell 的 GHERKAI_STEPS_DIR **不得**越过 definition（ADR 0037 决策 4：宿主一律从…** (1 connections) — `runtime/tests/test_detached_launcher.py`
- *... and 1 more nodes in this community*

## Relationships

- [Local Reconcile Loop Tests](Local_Reconcile_Loop_Tests.md) (11 shared connections)
- [Wall Clock Timestamps](Wall_Clock_Timestamps.md) (4 shared connections)
- [Job Domain Models](Job_Domain_Models.md) (3 shared connections)
- [Run Store Adapters](Run_Store_Adapters.md) (3 shared connections)
- [Tunnel Provider](Tunnel_Provider.md) (2 shared connections)
- [Cloud Store Adapters](Cloud_Store_Adapters.md) (2 shared connections)
- [Local Subprocess Launcher](Local_Subprocess_Launcher.md) (2 shared connections)
- [Engine Composition Root](Engine_Composition_Root.md) (2 shared connections)
- [Event Log Adapters](Event_Log_Adapters.md) (1 shared connections)
- [Reconciler Orchestration](Reconciler_Orchestration.md) (1 shared connections)
- [Tunnel Host Orchestration](Tunnel_Host_Orchestration.md) (1 shared connections)
- [SSM Path Naming](SSM_Path_Naming.md) (1 shared connections)

## Source Files

- `runtime/gherkai_runtime/detached.py`
- `runtime/tests/test_detached_launcher.py`

## Audit Trail

- EXTRACTED: 71 (96%)
- INFERRED: 3 (4%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*