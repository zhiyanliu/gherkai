# Subprocess Engine Adapter Tests

> 18 nodes · cohesion 0.29

## Key Concepts

- **test_subprocess_engine.py** (35 connections) — `core/tests/test_subprocess_engine.py`
- **_job()** (16 connections) — `core/tests/test_subprocess_engine.py`
- **_engine()** (12 connections) — `core/tests/test_subprocess_engine.py`
- **_rm()** (8 connections) — `core/tests/test_subprocess_engine.py`
- **test_adapter_network_error_with_schedule_classified_and_retried()** (7 connections) — `core/tests/test_subprocess_engine.py`
- **test_session_id_captured_from_scope_started_on_timeout()** (7 connections) — `core/tests/test_subprocess_engine.py`
- **test_silent_worker_timeout_fires_via_heartbeat()** (7 connections) — `core/tests/test_subprocess_engine.py`
- **test_adapter_crash_is_error()** (6 connections) — `core/tests/test_subprocess_engine.py`
- **test_adapter_with_schedule_pass()** (6 connections) — `core/tests/test_subprocess_engine.py`
- **test_log_sink_receives_worker_logs_and_keeps_stderr_clean()** (4 connections) — `core/tests/test_subprocess_engine.py`
- **Job** (3 connections)
- **test_adapter_network_exit_maps_to_network_error()** (3 connections) — `core/tests/test_subprocess_engine.py`
- **test_adapter_roundtrip_pass()** (3 connections) — `core/tests/test_subprocess_engine.py`
- **test_adapter_sigkill_backstop_on_deaf_worker()** (3 connections) — `core/tests/test_subprocess_engine.py`
- **test_adapter_stop_hanging_worker()** (3 connections) — `core/tests/test_subprocess_engine.py`
- **test_scope_started_carries_session_id()** (3 connections) — `core/tests/test_subprocess_engine.py`
- **子进程 Engine adapter 集成测试（ADR 0026 机制层）。 用 tests/fixtures/echo_worker.py 当真子进程…** (1 connections) — `core/tests/test_subprocess_engine.py`
- **log_sink（ADR 0041 决策二）：给了文件句柄，worker 的 stdout/stderr 透传全写 sink（无颜色码）、本进程 stderr…** (1 connections) — `core/tests/test_subprocess_engine.py`

## Relationships

- [Run Scheduling Core](Run_Scheduling_Core.md) (16 shared connections)
- [Job Domain Models](Job_Domain_Models.md) (13 shared connections)
- [Run Result Aggregation Tree](Run_Result_Aggregation_Tree.md) (4 shared connections)
- [Event Log Adapters](Event_Log_Adapters.md) (2 shared connections)
- [Log Pump and Redaction](Log_Pump_and_Redaction.md) (2 shared connections)
- [Typed Errors and Wire Protocol](Typed_Errors_and_Wire_Protocol.md) (2 shared connections)
- [Run State Projection](Run_State_Projection.md) (1 shared connections)

## Source Files

- `core/tests/test_subprocess_engine.py`

## Audit Trail

- EXTRACTED: 84 (100%)
- INFERRED: 0 (0%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*