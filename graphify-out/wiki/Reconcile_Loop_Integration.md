# Reconcile Loop Integration

> 16 nodes · cohesion 0.18

## Key Concepts

- **run_reconcile_loop()** (16 connections) — `runtime/gherkai_runtime/detached.py`
- **_setup()** (14 connections) — `runtime/tests/test_detached_launcher.py`
- **test_job_timeout_stops_worker_and_attributes_timeout()** (6 connections) — `runtime/tests/test_detached_launcher.py`
- **_echo_resolver()** (5 connections) — `runtime/tests/test_detached_launcher.py`
- **_now()** (5 connections) — `runtime/tests/test_detached_launcher.py`
- **test_crash_worker_finalizes_error()** (5 connections) — `runtime/tests/test_detached_launcher.py`
- **test_single_job_passes_end_to_end()** (5 connections) — `runtime/tests/test_detached_launcher.py`
- **test_two_jobs_concurrency_one()** (5 connections) — `runtime/tests/test_detached_launcher.py`
- **test_relay_recovers_foreign_timed_out_claim()** (4 connections) — `runtime/tests/test_detached_launcher.py`
- **per-run 进程的推进循环：反复 tick 直到全 done（ADR 0034 local 主力触发源）。…** (1 connections) — `runtime/gherkai_runtime/detached.py`
- **接力恢复（ADR 0034「job timeout」节 claimed_at ①）：他人 claim 的 RUNNING job（owner 进程已死、 无…** (1 connections) — `runtime/tests/test_detached_launcher.py`
- **echo_worker(crash) 非 0 退出 → task_exited 带非0 → project 判 error → run finalize…** (1 connections) — `runtime/tests/test_detached_launcher.py`
- **按 WORKER_MODE 起 echo_worker 的 SubprocessEngine，包成 resolver（所有 engine 名都映射到它）。** (1 connections) — `runtime/tests/test_detached_launcher.py`
- **真 spawn echo_worker(pass) → 事件落 SQLite → reconcile loop 推进到 passed 终态。** (1 connections) — `runtime/tests/test_detached_launcher.py`
- **max_concurrency=1：两 job 串行推进、都 passed。验 loop 起完一个再起下一个。** (1 connections) — `runtime/tests/test_detached_launcher.py`
- **job timeout local enforce 真跑（ADR 0034「job timeout」节）：silent worker…** (1 connections) — `runtime/tests/test_detached_launcher.py`

## Relationships

- [Detached Launcher Reconcile](Detached_Launcher_Reconcile.md) (10 shared connections)
- [Timestamp and Clock Utilities](Timestamp_and_Clock_Utilities.md) (3 shared connections)
- [DynamoDB RunStore Conditional Writes](DynamoDB_RunStore_Conditional_Writes.md) (3 shared connections)
- [Run State Rendering & Boto Guard](Run_State_Rendering_%26_Boto_Guard.md) (3 shared connections)
- [SQLite Event Log Store](SQLite_Event_Log_Store.md) (2 shared connections)
- [Subprocess Worker Launcher](Subprocess_Worker_Launcher.md) (2 shared connections)
- [Reconcile Ports & Tick](Reconcile_Ports_%26_Tick.md) (1 shared connections)
- [Run Result Verdict Model](Run_Result_Verdict_Model.md) (1 shared connections)
- [Local Detached Run Wiring](Local_Detached_Run_Wiring.md) (1 shared connections)
- [S3 ReportStore & Subprocess Engine](S3_ReportStore_%26_Subprocess_Engine.md) (1 shared connections)
- [SQLite Event Log & Projection](SQLite_Event_Log_%26_Projection.md) (1 shared connections)

## Source Files

- `runtime/gherkai_runtime/detached.py`
- `runtime/tests/test_detached_launcher.py`

## Audit Trail

- EXTRACTED: 44 (88%)
- INFERRED: 6 (12%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*