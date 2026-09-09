# Timestamp and Clock Utilities

> 9 nodes · cohesion 0.22

## Key Concepts

- **test_run_state_timestamps_share_one_format()** (13 connections) — `runtime/tests/test_detached_launcher.py`
- **parse_iso()** (5 connections) — `runtime/gherkai_runtime/compose.py`
- **_recover_timed_out_claims()** (4 connections) — `runtime/gherkai_runtime/detached.py`
- **now_iso()** (3 connections) — `runtime/gherkai_runtime/compose.py`
- **datetime** (2 connections)
- **`now_iso()` 的逆（两宿主共用一份）：解析回 aware datetime，供 claimed_at 超时判定做时间差。 容 `…Z`…** (1 connections) — `runtime/gherkai_runtime/compose.py`
- ****唯一的墙钟读取点**（组合根取时钟、core 不取，ADR 0027）：RunState/RunMeta 的一切时间戳走它。 三个宿主（cli 前台…** (1 connections) — `runtime/gherkai_runtime/compose.py`
- **接力恢复 deadline（ADR 0034「job timeout」节 claimed_at ①）：**他人 claim、本进程无 handle** 的…** (1 connections) — `runtime/gherkai_runtime/detached.py`
- **RunState 内时间戳**格式统一**（ADR 0034「时钟也只一份」）：submit 侧写的 started_at 与推进器写的…** (1 connections) — `runtime/tests/test_detached_launcher.py`

## Relationships

- [Composition Root Wiring](Composition_Root_Wiring.md) (3 shared connections)
- [Reconcile Loop Integration](Reconcile_Loop_Integration.md) (3 shared connections)
- [Run State Rendering & Boto Guard](Run_State_Rendering_%26_Boto_Guard.md) (2 shared connections)
- [Detached Launcher Reconcile](Detached_Launcher_Reconcile.md) (2 shared connections)
- [DynamoDB RunStore Conditional Writes](DynamoDB_RunStore_Conditional_Writes.md) (2 shared connections)
- [Local Detached Run Wiring](Local_Detached_Run_Wiring.md) (1 shared connections)
- [Subprocess Worker Launcher](Subprocess_Worker_Launcher.md) (1 shared connections)
- [SQLite Event Log Store](SQLite_Event_Log_Store.md) (1 shared connections)

## Source Files

- `runtime/gherkai_runtime/compose.py`
- `runtime/gherkai_runtime/detached.py`
- `runtime/tests/test_detached_launcher.py`

## Audit Trail

- EXTRACTED: 22 (96%)
- INFERRED: 1 (4%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*