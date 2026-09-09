# Subprocess Engine Tests

> 16 nodes · cohesion 0.34

## Key Concepts

- **test_subprocess_engine.py** (30 connections) — `core/tests/test_subprocess_engine.py`
- **_job()** (15 connections) — `core/tests/test_subprocess_engine.py`
- **_engine()** (12 connections) — `core/tests/test_subprocess_engine.py`
- **_rm()** (8 connections) — `core/tests/test_subprocess_engine.py`
- **test_adapter_network_error_with_schedule_classified_and_retried()** (7 connections) — `core/tests/test_subprocess_engine.py`
- **test_session_id_captured_from_scope_started_on_timeout()** (7 connections) — `core/tests/test_subprocess_engine.py`
- **test_silent_worker_timeout_fires_via_heartbeat()** (7 connections) — `core/tests/test_subprocess_engine.py`
- **test_adapter_crash_is_error()** (6 connections) — `core/tests/test_subprocess_engine.py`
- **test_adapter_with_schedule_pass()** (6 connections) — `core/tests/test_subprocess_engine.py`
- **test_adapter_network_exit_maps_to_network_error()** (3 connections) — `core/tests/test_subprocess_engine.py`
- **test_adapter_roundtrip_pass()** (3 connections) — `core/tests/test_subprocess_engine.py`
- **test_adapter_sigkill_backstop_on_deaf_worker()** (3 connections) — `core/tests/test_subprocess_engine.py`
- **test_adapter_stop_hanging_worker()** (3 connections) — `core/tests/test_subprocess_engine.py`
- **test_scope_started_carries_session_id()** (3 connections) — `core/tests/test_subprocess_engine.py`
- **Job** (2 connections)
- **子进程 Engine adapter 集成测试（ADR 0026 机制层）。 用 tests/fixtures/echo_worker.py 当真子进程…** (1 connections) — `core/tests/test_subprocess_engine.py`

## Relationships

- [Run Scheduling Engine](Run_Scheduling_Engine.md) (16 shared connections)
- [Engine Ports & Adapters](Engine_Ports_%26_Adapters.md) (8 shared connections)
- [Run Result Rendering](Run_Result_Rendering.md) (3 shared connections)
- [S3 Report Store & Subprocess](S3_Report_Store_%26_Subprocess.md) (2 shared connections)
- [Terminal Status Aggregation](Terminal_Status_Aggregation.md) (2 shared connections)
- [Event Progress Formatting](Event_Progress_Formatting.md) (1 shared connections)
- [State Projection & Planning](State_Projection_%26_Planning.md) (1 shared connections)
- [Boto Guard & S3 Offload](Boto_Guard_%26_S3_Offload.md) (1 shared connections)

## Source Files

- `core/tests/test_subprocess_engine.py`

## Audit Trail

- EXTRACTED: 75 (100%)
- INFERRED: 0 (0%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*