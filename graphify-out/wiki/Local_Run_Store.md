# Local Run Store

> 65 nodes · cohesion 0.05

## Key Concepts

- **LocalRunStore** (48 connections) — `core/gherkai_core/adapters/run_store/local.py`
- **test_detached_launcher.py** (26 connections) — `runtime/tests/test_detached_launcher.py`
- **build_local_reconcile()** (17 connections) — `runtime/gherkai_runtime/detached.py`
- **detached.py** (16 connections) — `runtime/gherkai_runtime/detached.py`
- **run_reconcile_loop()** (16 connections) — `runtime/gherkai_runtime/detached.py`
- **SubprocessLauncher** (15 connections) — `runtime/gherkai_runtime/detached.py`
- **_setup()** (14 connections) — `runtime/tests/test_detached_launcher.py`
- **test_run_state_timestamps_share_one_format()** (13 connections) — `runtime/tests/test_detached_launcher.py`
- **_seed_for_build()** (10 connections) — `runtime/tests/test_detached_launcher.py`
- **_job()** (9 connections) — `runtime/tests/test_detached_launcher.py`
- **test_build_local_reconcile_reads_steps_dir_from_definition()** (8 connections) — `runtime/tests/test_detached_launcher.py`
- **test_build_local_reconcile_resolves_region_like_foreground()** (8 connections) — `runtime/tests/test_detached_launcher.py`
- **._locked_rmw()** (7 connections) — `core/gherkai_core/adapters/run_store/local.py`
- **test_job_timeout_stops_worker_and_attributes_timeout()** (6 connections) — `runtime/tests/test_detached_launcher.py`
- **_echo_resolver()** (5 connections) — `runtime/tests/test_detached_launcher.py`
- **_now()** (5 connections) — `runtime/tests/test_detached_launcher.py`
- **test_crash_worker_finalizes_error()** (5 connections) — `runtime/tests/test_detached_launcher.py`
- **test_single_job_passes_end_to_end()** (5 connections) — `runtime/tests/test_detached_launcher.py`
- **test_two_jobs_concurrency_one()** (5 connections) — `runtime/tests/test_detached_launcher.py`
- **.load_run_meta()** (4 connections) — `core/gherkai_core/adapters/run_store/local.py`
- **.project_state()** (4 connections) — `core/gherkai_core/adapters/run_store/local.py`
- **.try_finalize()** (4 connections) — `core/gherkai_core/adapters/run_store/local.py`
- **_recover_timed_out_claims()** (4 connections) — `runtime/gherkai_runtime/detached.py`
- **test_build_local_reconcile_falls_back_to_flag_when_meta_missing()** (4 connections) — `runtime/tests/test_detached_launcher.py`
- **test_build_local_reconcile_no_steps_dir_when_definition_has_none()** (4 connections) — `runtime/tests/test_detached_launcher.py`
- *... and 40 more nodes in this community*

## Relationships

- [Run State Rendering](Run_State_Rendering.md) (35 shared connections)
- [Run Result Rendering](Run_Result_Rendering.md) (12 shared connections)
- [SQLite Event Log](SQLite_Event_Log.md) (9 shared connections)
- [Engine Ports & Adapters](Engine_Ports_%26_Adapters.md) (9 shared connections)
- [Local Result Store](Local_Result_Store.md) (6 shared connections)
- [SSM Path & Client Composition](SSM_Path_%26_Client_Composition.md) (5 shared connections)
- [Boto Guard & S3 Offload](Boto_Guard_%26_S3_Offload.md) (3 shared connections)
- [S3 Report Store & Subprocess](S3_Report_Store_%26_Subprocess.md) (3 shared connections)
- [Tunnel Cleanup](Tunnel_Cleanup.md) (2 shared connections)
- [Engine Composition Helpers](Engine_Composition_Helpers.md) (2 shared connections)
- [Report Refs & Results](Report_Refs_%26_Results.md) (2 shared connections)
- [Run Store Fixtures](Run_Store_Fixtures.md) (1 shared connections)

## Source Files

- `core/gherkai_core/adapters/run_store/__init__.py`
- `core/gherkai_core/adapters/run_store/local.py`
- `runtime/gherkai_runtime/detached.py`
- `runtime/tests/test_detached_launcher.py`

## Audit Trail

- EXTRACTED: 186 (90%)
- INFERRED: 20 (10%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*