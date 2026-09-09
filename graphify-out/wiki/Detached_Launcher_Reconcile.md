# Detached Launcher Reconcile

> 17 nodes · cohesion 0.20

## Key Concepts

- **test_detached_launcher.py** (26 connections) — `runtime/tests/test_detached_launcher.py`
- **build_local_reconcile()** (17 connections) — `runtime/gherkai_runtime/detached.py`
- **_seed_for_build()** (10 connections) — `runtime/tests/test_detached_launcher.py`
- **_job()** (9 connections) — `runtime/tests/test_detached_launcher.py`
- **test_build_local_reconcile_reads_steps_dir_from_definition()** (8 connections) — `runtime/tests/test_detached_launcher.py`
- **test_build_local_reconcile_resolves_region_like_foreground()** (8 connections) — `runtime/tests/test_detached_launcher.py`
- **test_build_local_reconcile_falls_back_to_flag_when_meta_missing()** (4 connections) — `runtime/tests/test_detached_launcher.py`
- **test_build_local_reconcile_no_steps_dir_when_definition_has_none()** (4 connections) — `runtime/tests/test_detached_launcher.py`
- **test_build_local_reconcile_prefers_meta_max_concurrency()** (4 connections) — `runtime/tests/test_detached_launcher.py`
- **从本地落点重建 per-run reconcile 所需的全部（meta 从 RunStore 读回、log/store/launcher 重建）。 per-…** (1 connections) — `runtime/gherkai_runtime/detached.py`
- **SubprocessLauncher + reconcile loop 真跑集成测试（ADR 0034 P3b）。 **真 spawn echo_worker…** (1 connections) — `runtime/tests/test_detached_launcher.py`
- **region 走与前台 run 相同的解析链（ADR 0016 决策 C）：不显式给 --region 时 env/profile config 兜底、…** (1 connections) — `runtime/tests/test_detached_launcher.py`
- **落一个最小 run（单 pending job）供 build_local_reconcile 读回，meta 的 max_concurrency 按参数。** (1 connections) — `runtime/tests/test_detached_launcher.py`
- **并发上限以 definition 为准（ADR 0034 机制四）：入参 flag 与 meta 冲突时用 meta——`status --wait` 接力者…** (1 connections) — `runtime/tests/test_detached_launcher.py`
- **对偶（防「恒取入参」的假绿反面）：meta 无值（打通前落的旧 definition）→ 回落入参 flag。** (1 connections) — `runtime/tests/test_detached_launcher.py`
- **使用方 step 目录随 definition 走（ADR 0037 决策 4）：宿主从 RunStore 读回 meta.steps_dir、 经 env…** (1 connections) — `runtime/tests/test_detached_launcher.py`
- **对偶（防「恒注入」假绿）：definition 无 steps_dir（未给/旧落盘/cloud 档）→ 宿主不注入该 env， 即便宿主 CWD 下恰好有个…** (1 connections) — `runtime/tests/test_detached_launcher.py`

## Relationships

- [Reconcile Loop Integration](Reconcile_Loop_Integration.md) (10 shared connections)
- [DynamoDB RunStore Conditional Writes](DynamoDB_RunStore_Conditional_Writes.md) (7 shared connections)
- [Run State Rendering & Boto Guard](Run_State_Rendering_%26_Boto_Guard.md) (7 shared connections)
- [Engine Ports & Adapters](Engine_Ports_%26_Adapters.md) (5 shared connections)
- [Local Detached Run Wiring](Local_Detached_Run_Wiring.md) (3 shared connections)
- [Engine Resolver Building](Engine_Resolver_Building.md) (2 shared connections)
- [Subprocess Worker Launcher](Subprocess_Worker_Launcher.md) (2 shared connections)
- [Timestamp and Clock Utilities](Timestamp_and_Clock_Utilities.md) (2 shared connections)
- [Cloud Target Resolution](Cloud_Target_Resolution.md) (1 shared connections)
- [SQLite Event Log Store](SQLite_Event_Log_Store.md) (1 shared connections)
- [Run Persistence Orchestration](Run_Persistence_Orchestration.md) (1 shared connections)
- [Render & ReportStore Local](Render_%26_ReportStore_Local.md) (1 shared connections)

## Source Files

- `runtime/gherkai_runtime/detached.py`
- `runtime/tests/test_detached_launcher.py`

## Audit Trail

- EXTRACTED: 69 (97%)
- INFERRED: 2 (3%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*