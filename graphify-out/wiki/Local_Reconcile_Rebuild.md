# Local Reconcile Rebuild

> 23 nodes · cohesion 0.11

## Key Concepts

- **build_local_reconcile()** (20 connections) — `runtime/gherkai_runtime/detached.py`
- **_seed_for_build()** (13 connections) — `runtime/tests/test_detached_launcher.py`
- **_job()** (10 connections) — `runtime/tests/test_detached_launcher.py`
- **test_build_local_reconcile_reads_steps_dir_from_definition()** (8 connections) — `runtime/tests/test_detached_launcher.py`
- **test_build_local_reconcile_resolves_region_like_foreground()** (8 connections) — `runtime/tests/test_detached_launcher.py`
- **test_drive_local_reconcile_drives_to_terminal_then_tears_down_tunnel()** (6 connections) — `runtime/tests/test_detached_launcher.py`
- **test_build_local_reconcile_falls_back_to_flag_when_meta_missing()** (4 connections) — `runtime/tests/test_detached_launcher.py`
- **test_build_local_reconcile_goes_through_resolve_aws_identity()** (4 connections) — `runtime/tests/test_detached_launcher.py`
- **test_build_local_reconcile_host_env_steps_dir_does_not_leak()** (4 connections) — `runtime/tests/test_detached_launcher.py`
- **test_build_local_reconcile_no_steps_dir_when_definition_has_none()** (4 connections) — `runtime/tests/test_detached_launcher.py`
- **test_build_local_reconcile_prefers_meta_max_concurrency()** (4 connections) — `runtime/tests/test_detached_launcher.py`
- **_paths()** (3 connections) — `runtime/gherkai_runtime/detached.py`
- **local 无状态批量运行的落点：events SQLite 与 RunStore/ResultStore 同在 <report_dir>/<run_id>/。** (1 connections) — `runtime/gherkai_runtime/detached.py`
- **从本地落点重建 per-run reconcile 所需的全部（meta 从 RunStore 读回、log/store/launcher 重建）。 per-…** (1 connections) — `runtime/gherkai_runtime/detached.py`
- **region 走与前台 run 相同的解析链（ADR 0016 决策 C）：不显式给 --region 时 env/profile config 兜底、…** (1 connections) — `runtime/tests/test_detached_launcher.py`
- **后台重建端与前台 run 共用**同一个** region/profile 解析实现（ADR 0016 决策 C）：本函数不自写一份。 换掉…** (1 connections) — `runtime/tests/test_detached_launcher.py`
- **落一个最小 run（单 pending job）供 build_local_reconcile 读回，meta 的 max_concurrency 按参数。** (1 connections) — `runtime/tests/test_detached_launcher.py`
- **并发上限以 definition 为准（ADR 0034 机制四）：入参 flag 与 meta 冲突时用 meta——`status --wait` 接力者…** (1 connections) — `runtime/tests/test_detached_launcher.py`
- **对偶（防「恒取入参」的假绿反面）：meta 无值（打通前落的旧 definition）→ 回落入参 flag。** (1 connections) — `runtime/tests/test_detached_launcher.py`
- **使用方 step 目录随 definition 走（ADR 0037 决策 4）：宿主从 RunStore 读回 meta.steps_dir、 经 env…** (1 connections) — `runtime/tests/test_detached_launcher.py`
- **对偶（防「恒注入」假绿）：definition 无 steps_dir（未给/旧落盘/云端后端）→ 宿主不注入该 env， 即便宿主 CWD 下恰好有个…** (1 connections) — `runtime/tests/test_detached_launcher.py`
- **接力者 shell 的 GHERKAI_STEPS_DIR **不得**越过 definition（ADR 0037 决策 4：宿主一律从…** (1 connections) — `runtime/tests/test_detached_launcher.py`
- **local 推进唯一入口的三步护栏（ADR 0034 三宿主同一套机制 + ADR 0035「终态即拆」）：装配 → 推到终态 → 拆隧道。 只把引擎替成…** (1 connections) — `runtime/tests/test_detached_launcher.py`

## Relationships

- [Detached Launcher Tests](Detached_Launcher_Tests.md) (12 shared connections)
- [Run Metadata & S3 Offload](Run_Metadata_%26_S3_Offload.md) (6 shared connections)
- [Run State Rendering](Run_State_Rendering.md) (6 shared connections)
- [Local & S3 Result Stores](Local_%26_S3_Result_Stores.md) (5 shared connections)
- [Local Detached Execution](Local_Detached_Execution.md) (4 shared connections)
- [Engine Composition Root](Engine_Composition_Root.md) (2 shared connections)
- [Subprocess Engine Launcher](Subprocess_Engine_Launcher.md) (2 shared connections)
- [Timestamps & Wallclock](Timestamps_%26_Wallclock.md) (2 shared connections)
- [Worker Locator & AWS Resolution](Worker_Locator_%26_AWS_Resolution.md) (1 shared connections)
- [SQLite Event Log](SQLite_Event_Log.md) (1 shared connections)
- [Local Result Store](Local_Result_Store.md) (1 shared connections)
- [Local Report Store](Local_Report_Store.md) (1 shared connections)

## Source Files

- `runtime/gherkai_runtime/detached.py`
- `runtime/tests/test_detached_launcher.py`

## Audit Trail

- EXTRACTED: 69 (97%)
- INFERRED: 2 (3%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*