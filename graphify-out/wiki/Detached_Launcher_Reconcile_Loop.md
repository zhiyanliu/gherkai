# Detached Launcher Reconcile Loop

> 20 nodes · cohesion 0.20

## Key Concepts

- **test_detached_launcher.py** (32 connections) — `runtime/tests/test_detached_launcher.py`
- **run_reconcile_loop()** (20 connections) — `runtime/gherkai_runtime/detached.py`
- **_setup()** (15 connections) — `runtime/tests/test_detached_launcher.py`
- **_echo_resolver()** (7 connections) — `runtime/tests/test_detached_launcher.py`
- **test_grace_query_failure_never_spawns_a_worker()** (7 connections) — `runtime/tests/test_detached_launcher.py`
- **_now()** (6 connections) — `runtime/tests/test_detached_launcher.py`
- **test_job_timeout_stops_worker_and_attributes_timeout()** (6 connections) — `runtime/tests/test_detached_launcher.py`
- **test_crash_worker_finalizes_error()** (5 connections) — `runtime/tests/test_detached_launcher.py`
- **test_single_job_passes_end_to_end()** (5 connections) — `runtime/tests/test_detached_launcher.py`
- **test_two_jobs_concurrency_one()** (5 connections) — `runtime/tests/test_detached_launcher.py`
- **test_relay_recovers_foreign_timed_out_claim()** (4 connections) — `runtime/tests/test_detached_launcher.py`
- **per-run 进程的推进循环：反复 tick 直到全 done（ADR 0034 local 主力触发源）。…** (1 connections) — `runtime/gherkai_runtime/detached.py`
- **SubprocessLauncher + reconcile loop 真实运行集成测试（ADR 0034 本机后端）。 **真 spawn…** (1 connections) — `runtime/tests/test_detached_launcher.py`
- **接力恢复（ADR 0034「job timeout」节 claimed_at ①）：他人 claim 的 RUNNING job（owner 进程已死、 无…** (1 connections) — `runtime/tests/test_detached_launcher.py`
- **grace 下限现在要 spawn 一次 worker 自述才问得到、**会抛**（ADR 0024「引擎自报下限」：旧 worker 不认入口 / 定位不到…** (1 connections) — `runtime/tests/test_detached_launcher.py`
- **echo_worker(crash) 非 0 退出 → task_exited 带非0 → project 判 error → run finalize…** (1 connections) — `runtime/tests/test_detached_launcher.py`
- **按 WORKER_MODE 起 echo_worker 的 SubprocessEngine，包成 resolver（所有 engine 名都映射到它）。** (1 connections) — `runtime/tests/test_detached_launcher.py`
- **真 spawn echo_worker(pass) → 事件落 SQLite → reconcile loop 推进到 passed 终态。** (1 connections) — `runtime/tests/test_detached_launcher.py`
- **max_concurrency=1：两 job 串行推进、都 passed。验 loop 起完一个再起下一个。** (1 connections) — `runtime/tests/test_detached_launcher.py`
- **job timeout local enforce 真实运行（ADR 0034「job timeout」节）：silent worker…** (1 connections) — `runtime/tests/test_detached_launcher.py`

## Relationships

- [Local Reconcile Rebuild](Local_Reconcile_Rebuild.md) (11 shared connections)
- [Timestamp & Wallclock Utils](Timestamp_%26_Wallclock_Utils.md) (8 shared connections)
- [Detached Local Run Host](Detached_Local_Run_Host.md) (5 shared connections)
- [Subprocess Engine & Launcher](Subprocess_Engine_%26_Launcher.md) (5 shared connections)
- [Run State Store](Run_State_Store.md) (4 shared connections)
- [Reconciler Event Projection](Reconciler_Event_Projection.md) (2 shared connections)
- [SQLite Event Log](SQLite_Event_Log.md) (2 shared connections)
- [Job Explain Data Model](Job_Explain_Data_Model.md) (2 shared connections)
- [EventLog And Launcher Ports](EventLog_And_Launcher_Ports.md) (1 shared connections)
- [Subprocess Engine Adapter](Subprocess_Engine_Adapter.md) (1 shared connections)
- [Cloud Adapter Boundary Modules](Cloud_Adapter_Boundary_Modules.md) (1 shared connections)
- [SSM Paths And Compose](SSM_Paths_And_Compose.md) (1 shared connections)

## Source Files

- `runtime/gherkai_runtime/detached.py`
- `runtime/tests/test_detached_launcher.py`

## Audit Trail

- EXTRACTED: 76 (92%)
- INFERRED: 7 (8%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*