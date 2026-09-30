# Wall Clock Timestamps

> 19 nodes · cohesion 0.12

## Key Concepts

- **test_report_still_written_when_the_run_duration_read_fails()** (13 connections) — `runtime/tests/test_detached_launcher.py`
- **test_run_state_timestamps_share_one_format()** (13 connections) — `runtime/tests/test_detached_launcher.py`
- **_job()** (10 connections) — `runtime/tests/test_detached_launcher.py`
- **test_build_local_reconcile_reads_steps_dir_from_definition()** (8 connections) — `runtime/tests/test_detached_launcher.py`
- **test_build_local_reconcile_resolves_region_like_foreground()** (8 connections) — `runtime/tests/test_detached_launcher.py`
- **parse_iso()** (6 connections) — `runtime/gherkai_runtime/compose.py`
- **run_duration_ms()** (6 connections) — `runtime/gherkai_runtime/compose.py`
- **now_iso()** (4 connections) — `runtime/gherkai_runtime/compose.py`
- **_recover_timed_out_claims()** (4 connections) — `runtime/gherkai_runtime/detached.py`
- **test_run_duration_ms_from_run_state_timestamps()** (3 connections) — `runtime/tests/test_compose.py`
- **datetime** (2 connections)
- **detached run 的 run 级墙钟（毫秒），取 RunState `ended_at` 减 `started_at`（提交落库到 finalize…** (1 connections) — `runtime/gherkai_runtime/compose.py`
- ****唯一的墙钟读取点**（组合根取时钟、core 不取，ADR 0027）：RunState/RunMeta 的一切时间戳走它。 三个宿主（cli 前台…** (1 connections) — `runtime/gherkai_runtime/compose.py`
- **`now_iso()` 的逆（两宿主共用一份）：解析回 aware datetime，供 claimed_at 超时判定做时间差。 容 `…Z`…** (1 connections) — `runtime/gherkai_runtime/compose.py`
- **接力恢复 deadline（ADR 0034「job timeout」节 claimed_at ①）：**他人 claim、本进程无 handle** 的…** (1 connections) — `runtime/gherkai_runtime/detached.py`
- **run 级墙钟取数失败不得连坐报告收尾（ADR 0030 决定三：commit point 之后的失败无人重试）。 墙钟是派生指标，取它要在 finalize…** (1 connections) — `runtime/tests/test_detached_launcher.py`
- **region 走与前台 run 相同的解析链（ADR 0016 决策 C）：不显式给 --region 时 env/profile config 兜底、…** (1 connections) — `runtime/tests/test_detached_launcher.py`
- **使用方 step 目录随 definition 走（ADR 0037 决策 4）：宿主从 RunStore 读回 meta.steps_dir、 经 env…** (1 connections) — `runtime/tests/test_detached_launcher.py`
- **RunState 内时间戳**格式统一**（ADR 0034「时钟也只一份」）：submit 侧写的 started_at 与推进器写的…** (1 connections) — `runtime/tests/test_detached_launcher.py`

## Relationships

- [Local Reconcile Loop Tests](Local_Reconcile_Loop_Tests.md) (12 shared connections)
- [Job Domain Models](Job_Domain_Models.md) (7 shared connections)
- [Run State Store](Run_State_Store.md) (5 shared connections)
- [SSM Path Naming](SSM_Path_Naming.md) (4 shared connections)
- [Local Detached Execution](Local_Detached_Execution.md) (4 shared connections)
- [Run Store Adapters](Run_Store_Adapters.md) (4 shared connections)
- [Cloud Store Adapters](Cloud_Store_Adapters.md) (4 shared connections)
- [Local Subprocess Launcher](Local_Subprocess_Launcher.md) (2 shared connections)
- [SQLite Event Log](SQLite_Event_Log.md) (2 shared connections)
- [Cloud Resource Resolution](Cloud_Resource_Resolution.md) (1 shared connections)

## Source Files

- `runtime/gherkai_runtime/compose.py`
- `runtime/gherkai_runtime/detached.py`
- `runtime/tests/test_compose.py`
- `runtime/tests/test_detached_launcher.py`

## Audit Trail

- EXTRACTED: 62 (95%)
- INFERRED: 3 (5%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*