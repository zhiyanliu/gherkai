# Run Duration & Claims

> 8 nodes · cohesion 0.25

## Key Concepts

- **parse_iso()** (6 connections) — `runtime/gherkai_runtime/compose.py`
- **run_duration_ms()** (6 connections) — `runtime/gherkai_runtime/compose.py`
- **_recover_timed_out_claims()** (4 connections) — `runtime/gherkai_runtime/detached.py`
- **test_run_duration_ms_from_run_state_timestamps()** (3 connections) — `runtime/tests/test_compose.py`
- **datetime** (2 connections)
- **detached run 的 run 级墙钟（毫秒），取 RunState `ended_at` 减 `started_at`（提交落库到 finalize…** (1 connections) — `runtime/gherkai_runtime/compose.py`
- **`now_iso()` 的逆（两宿主共用一份）：解析回 aware datetime，供 claimed_at 超时判定做时间差。 容 `…Z`…** (1 connections) — `runtime/gherkai_runtime/compose.py`
- **接力恢复 deadline（ADR 0034「job timeout」节 claimed_at ①）：**他人 claim、本进程无 handle** 的…** (1 connections) — `runtime/gherkai_runtime/detached.py`

## Relationships

- [Cloud Composition Helpers](Cloud_Composition_Helpers.md) (3 shared connections)
- [Wallclock Timestamp Source](Wallclock_Timestamp_Source.md) (2 shared connections)
- [Detached Reconcile Loop Tests](Detached_Reconcile_Loop_Tests.md) (2 shared connections)
- [Local Detached Reconcile](Local_Detached_Reconcile.md) (1 shared connections)
- [Composition Root Helpers](Composition_Root_Helpers.md) (1 shared connections)
- [Run State Rendering](Run_State_Rendering.md) (1 shared connections)

## Source Files

- `runtime/gherkai_runtime/compose.py`
- `runtime/gherkai_runtime/detached.py`
- `runtime/tests/test_compose.py`

## Audit Trail

- EXTRACTED: 16 (94%)
- INFERRED: 1 (6%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*