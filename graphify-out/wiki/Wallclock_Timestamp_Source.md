# Wallclock Timestamp Source

> 11 nodes · cohesion 0.20

## Key Concepts

- **test_report_still_written_when_the_run_duration_read_fails()** (13 connections) — `runtime/tests/test_detached_launcher.py`
- **test_run_state_timestamps_share_one_format()** (13 connections) — `runtime/tests/test_detached_launcher.py`
- **_job()** (10 connections) — `runtime/tests/test_detached_launcher.py`
- **test_build_local_reconcile_reads_steps_dir_from_definition()** (8 connections) — `runtime/tests/test_detached_launcher.py`
- **test_build_local_reconcile_resolves_region_like_foreground()** (8 connections) — `runtime/tests/test_detached_launcher.py`
- **now_iso()** (4 connections) — `runtime/gherkai_runtime/compose.py`
- ****唯一的墙钟读取点**（组合根取时钟、core 不取，ADR 0027）：RunState/RunMeta 的一切时间戳走它。 三个宿主（cli 前台…** (1 connections) — `runtime/gherkai_runtime/compose.py`
- **run 级墙钟取数失败不得连坐报告收尾（ADR 0030 决定三：commit point 之后的失败无人重试）。 墙钟是派生指标，取它要在 finalize…** (1 connections) — `runtime/tests/test_detached_launcher.py`
- **region 走与前台 run 相同的解析链（ADR 0016 决策 C）：不显式给 --region 时 env/profile config 兜底、…** (1 connections) — `runtime/tests/test_detached_launcher.py`
- **使用方 step 目录随 definition 走（ADR 0037 决策 4）：宿主从 RunStore 读回 meta.steps_dir、 经 env…** (1 connections) — `runtime/tests/test_detached_launcher.py`
- **RunState 内时间戳**格式统一**（ADR 0034「时钟也只一份」）：submit 侧写的 started_at 与推进器写的…** (1 connections) — `runtime/tests/test_detached_launcher.py`

## Relationships

- [Detached Reconcile Loop Tests](Detached_Reconcile_Loop_Tests.md) (10 shared connections)
- [Run State Rendering](Run_State_Rendering.md) (8 shared connections)
- [Run Definition Domain Model](Run_Definition_Domain_Model.md) (7 shared connections)
- [DynamoDB Run Store](DynamoDB_Run_Store.md) (4 shared connections)
- [Local Reconcile Rebuild](Local_Reconcile_Rebuild.md) (3 shared connections)
- [Subprocess Launcher](Subprocess_Launcher.md) (2 shared connections)
- [Run Duration & Claims](Run_Duration_%26_Claims.md) (2 shared connections)
- [SQLite Event Log](SQLite_Event_Log.md) (2 shared connections)
- [Cloud Composition Helpers](Cloud_Composition_Helpers.md) (1 shared connections)

## Source Files

- `runtime/gherkai_runtime/compose.py`
- `runtime/tests/test_detached_launcher.py`

## Audit Trail

- EXTRACTED: 48 (96%)
- INFERRED: 2 (4%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*