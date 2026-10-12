# Local Reconcile Rebuild

> 19 nodes · cohesion 0.14

## Key Concepts

- **build_local_reconcile()** (20 connections) — `runtime/gherkai_runtime/detached.py`
- **_seed_for_build()** (13 connections) — `runtime/tests/test_detached_launcher.py`
- **_job()** (10 connections) — `runtime/tests/test_detached_launcher.py`
- **test_build_local_reconcile_reads_steps_dir_from_definition()** (8 connections) — `runtime/tests/test_detached_launcher.py`
- **test_build_local_reconcile_resolves_region_like_foreground()** (8 connections) — `runtime/tests/test_detached_launcher.py`
- **test_build_local_reconcile_falls_back_to_flag_when_meta_missing()** (4 connections) — `runtime/tests/test_detached_launcher.py`
- **test_build_local_reconcile_goes_through_resolve_aws_identity()** (4 connections) — `runtime/tests/test_detached_launcher.py`
- **test_build_local_reconcile_host_env_steps_dir_does_not_leak()** (4 connections) — `runtime/tests/test_detached_launcher.py`
- **test_build_local_reconcile_no_steps_dir_when_definition_has_none()** (4 connections) — `runtime/tests/test_detached_launcher.py`
- **test_build_local_reconcile_prefers_meta_max_concurrency()** (4 connections) — `runtime/tests/test_detached_launcher.py`
- **从本地落点重建 per-run reconcile 所需的全部（meta 从 RunStore 读回、log/store/launcher 重建）。 per-…** (1 connections) — `runtime/gherkai_runtime/detached.py`
- **region 走与前台 run 相同的解析链（ADR 0016 决策 C）：不显式给 --region 时 env/profile config 兜底、…** (1 connections) — `runtime/tests/test_detached_launcher.py`
- **后台重建端与前台 run 共用**同一个** region/profile 解析实现（ADR 0016 决策 C）：本函数不自写一份。 换掉…** (1 connections) — `runtime/tests/test_detached_launcher.py`
- **落一个最小 run（单 pending job）供 build_local_reconcile 读回，meta 的 max_concurrency 按参数。** (1 connections) — `runtime/tests/test_detached_launcher.py`
- **并发上限以 definition 为准（ADR 0034 机制四）：入参 flag 与 meta 冲突时用 meta——`status --wait` 接力者…** (1 connections) — `runtime/tests/test_detached_launcher.py`
- **对偶（防「恒取入参」的假绿反面）：meta 无值（打通前落的旧 definition）→ 回落入参 flag。** (1 connections) — `runtime/tests/test_detached_launcher.py`
- **使用方 step 目录随 definition 走（ADR 0037 决策 4）：宿主从 RunStore 读回 meta.steps_dir、 经 env…** (1 connections) — `runtime/tests/test_detached_launcher.py`
- **对偶（防「恒注入」假绿）：definition 无 steps_dir（未给/旧落盘/云端后端）→ 宿主不注入该 env， 即便宿主 CWD 下恰好有个…** (1 connections) — `runtime/tests/test_detached_launcher.py`
- **接力者 shell 的 GHERKAI_STEPS_DIR **不得**越过 definition（ADR 0037 决策 4：宿主一律从…** (1 connections) — `runtime/tests/test_detached_launcher.py`

## Relationships

- [Detached Launcher Reconcile Loop](Detached_Launcher_Reconcile_Loop.md) (11 shared connections)
- [Run State Store](Run_State_Store.md) (7 shared connections)
- [Job Explain Data Model](Job_Explain_Data_Model.md) (6 shared connections)
- [Detached Local Run Host](Detached_Local_Run_Host.md) (4 shared connections)
- [DynamoDB Job State Store](DynamoDB_Job_State_Store.md) (3 shared connections)
- [Local Compose Root](Local_Compose_Root.md) (2 shared connections)
- [Timestamp & Wallclock Utils](Timestamp_%26_Wallclock_Utils.md) (2 shared connections)
- [AWS Target Resolution](AWS_Target_Resolution.md) (1 shared connections)
- [SQLite Event Log](SQLite_Event_Log.md) (1 shared connections)
- [Subprocess Engine & Launcher](Subprocess_Engine_%26_Launcher.md) (1 shared connections)
- [Run Persistence Local Stores](Run_Persistence_Local_Stores.md) (1 shared connections)
- [Explain Reads And Report Store](Explain_Reads_And_Report_Store.md) (1 shared connections)

## Source Files

- `runtime/gherkai_runtime/detached.py`
- `runtime/tests/test_detached_launcher.py`

## Audit Trail

- EXTRACTED: 62 (97%)
- INFERRED: 2 (3%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*