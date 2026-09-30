# Local Reconcile Rebuild

> 14 nodes · cohesion 0.19

## Key Concepts

- **build_local_reconcile()** (20 connections) — `runtime/gherkai_runtime/detached.py`
- **_seed_for_build()** (13 connections) — `runtime/tests/test_detached_launcher.py`
- **test_build_local_reconcile_falls_back_to_flag_when_meta_missing()** (4 connections) — `runtime/tests/test_detached_launcher.py`
- **test_build_local_reconcile_goes_through_resolve_aws_identity()** (4 connections) — `runtime/tests/test_detached_launcher.py`
- **test_build_local_reconcile_host_env_steps_dir_does_not_leak()** (4 connections) — `runtime/tests/test_detached_launcher.py`
- **test_build_local_reconcile_no_steps_dir_when_definition_has_none()** (4 connections) — `runtime/tests/test_detached_launcher.py`
- **test_build_local_reconcile_prefers_meta_max_concurrency()** (4 connections) — `runtime/tests/test_detached_launcher.py`
- **从本地落点重建 per-run reconcile 所需的全部（meta 从 RunStore 读回、log/store/launcher 重建）。 per-…** (1 connections) — `runtime/gherkai_runtime/detached.py`
- **后台重建端与前台 run 共用**同一个** region/profile 解析实现（ADR 0016 决策 C）：本函数不自写一份。 换掉…** (1 connections) — `runtime/tests/test_detached_launcher.py`
- **落一个最小 run（单 pending job）供 build_local_reconcile 读回，meta 的 max_concurrency 按参数。** (1 connections) — `runtime/tests/test_detached_launcher.py`
- **并发上限以 definition 为准（ADR 0034 机制四）：入参 flag 与 meta 冲突时用 meta——`status --wait` 接力者…** (1 connections) — `runtime/tests/test_detached_launcher.py`
- **对偶（防「恒取入参」的假绿反面）：meta 无值（打通前落的旧 definition）→ 回落入参 flag。** (1 connections) — `runtime/tests/test_detached_launcher.py`
- **对偶（防「恒注入」假绿）：definition 无 steps_dir（未给/旧落盘/云端后端）→ 宿主不注入该 env， 即便宿主 CWD 下恰好有个…** (1 connections) — `runtime/tests/test_detached_launcher.py`
- **接力者 shell 的 GHERKAI_STEPS_DIR **不得**越过 definition（ADR 0037 决策 4：宿主一律从…** (1 connections) — `runtime/tests/test_detached_launcher.py`

## Relationships

- [Detached Reconcile Loop Tests](Detached_Reconcile_Loop_Tests.md) (7 shared connections)
- [Local Detached Reconcile](Local_Detached_Reconcile.md) (4 shared connections)
- [Run State Rendering](Run_State_Rendering.md) (3 shared connections)
- [Wallclock Timestamp Source](Wallclock_Timestamp_Source.md) (3 shared connections)
- [AWS Target Resolution](AWS_Target_Resolution.md) (1 shared connections)
- [SQLite Event Log](SQLite_Event_Log.md) (1 shared connections)
- [Composition Root Helpers](Composition_Root_Helpers.md) (1 shared connections)
- [Cloud Engine Resolver Build](Cloud_Engine_Resolver_Build.md) (1 shared connections)
- [Subprocess Launcher](Subprocess_Launcher.md) (1 shared connections)
- [Run Persistence Orchestration](Run_Persistence_Orchestration.md) (1 shared connections)
- [Report Store Adapters](Report_Store_Adapters.md) (1 shared connections)
- [Run Definition Domain Model](Run_Definition_Domain_Model.md) (1 shared connections)

## Source Files

- `runtime/gherkai_runtime/detached.py`
- `runtime/tests/test_detached_launcher.py`

## Audit Trail

- EXTRACTED: 41 (95%)
- INFERRED: 2 (5%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*