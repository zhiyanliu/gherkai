# Subprocess Engine Logging

> 28 nodes · cohesion 0.15

## Key Concepts

- **test_subprocess_engine.py** (39 connections) — `core/tests/test_subprocess_engine.py`
- **_job()** (16 connections) — `core/tests/test_subprocess_engine.py`
- **_engine()** (12 connections) — `core/tests/test_subprocess_engine.py`
- **_pump_log()** (9 connections) — `core/gherkai_core/adapters/subprocess_engine.py`
- **_rm()** (8 connections) — `core/tests/test_subprocess_engine.py`
- **test_adapter_network_error_with_schedule_classified_and_retried()** (7 connections) — `core/tests/test_subprocess_engine.py`
- **test_session_id_captured_from_scope_started_on_timeout()** (7 connections) — `core/tests/test_subprocess_engine.py`
- **test_silent_worker_timeout_fires_via_heartbeat()** (7 connections) — `core/tests/test_subprocess_engine.py`
- **test_adapter_crash_is_error()** (6 connections) — `core/tests/test_subprocess_engine.py`
- **test_adapter_with_schedule_pass()** (6 connections) — `core/tests/test_subprocess_engine.py`
- **_scope_color()** (5 connections) — `core/gherkai_core/adapters/subprocess_engine.py`
- **test_log_sink_receives_worker_logs_and_keeps_stderr_clean()** (4 connections) — `core/tests/test_subprocess_engine.py`
- **Job** (3 connections)
- **test_adapter_network_exit_maps_to_network_error()** (3 connections) — `core/tests/test_subprocess_engine.py`
- **test_adapter_roundtrip_pass()** (3 connections) — `core/tests/test_subprocess_engine.py`
- **test_adapter_sigkill_backstop_on_deaf_worker()** (3 connections) — `core/tests/test_subprocess_engine.py`
- **test_adapter_stop_hanging_worker()** (3 connections) — `core/tests/test_subprocess_engine.py`
- **test_pump_log_masks_tunnel_credentials_in_sink_and_stderr()** (3 connections) — `core/tests/test_subprocess_engine.py`
- **test_scope_started_carries_session_id()** (3 connections) — `core/tests/test_subprocess_engine.py`
- **test_palette_excludes_verdict_and_default_colors()** (2 connections) — `core/tests/test_subprocess_engine.py`
- **test_pump_log_colors_prefix_only_when_policy_says_so()** (2 connections) — `core/tests/test_subprocess_engine.py`
- **test_scope_colors_assigned_in_order_without_collision_and_stable()** (2 connections) — `core/tests/test_subprocess_engine.py`
- **scope 的前缀色：首次出现时按出现顺序取下一色，之后恒同色（进程内注册表，一次 run 一个进程）。** (1 connections) — `core/gherkai_core/adapters/subprocess_engine.py`
- **把 worker 的 stdout（SDK 噪声，tag=out）/ stderr（诊断，tag=err）实时透传为本进程日志。 带 [worker…** (1 connections) — `core/gherkai_core/adapters/subprocess_engine.py`
- **子进程 Engine adapter 集成测试（ADR 0026 机制层）。 用 tests/fixtures/echo_worker.py 当真子进程…** (1 connections) — `core/tests/test_subprocess_engine.py`
- *... and 3 more nodes in this community*

## Relationships

- [Schedule Module Tests](Schedule_Module_Tests.md) (16 shared connections)
- [Job/Scenario Explain Model](Job-Scenario_Explain_Model.md) (10 shared connections)
- [SQLite Event Log Adapter](SQLite_Event_Log_Adapter.md) (6 shared connections)
- [Cloud Launcher & Fargate Adapters](Cloud_Launcher_%26_Fargate_Adapters.md) (5 shared connections)
- [Subprocess Worker Handle](Subprocess_Worker_Handle.md) (2 shared connections)
- [Explain JSON & Redaction](Explain_JSON_%26_Redaction.md) (1 shared connections)
- [Terminal Color Policy](Terminal_Color_Policy.md) (1 shared connections)
- [Event Progress Formatting](Event_Progress_Formatting.md) (1 shared connections)
- [Fake DDB Table & SQLite Records](Fake_DDB_Table_%26_SQLite_Records.md) (1 shared connections)
- [Severity Aggregation & Fake Engine](Severity_Aggregation_%26_Fake_Engine.md) (1 shared connections)
- [Test Fixtures & Conftest](Test_Fixtures_%26_Conftest.md) (1 shared connections)

## Source Files

- `core/gherkai_core/adapters/subprocess_engine.py`
- `core/tests/test_subprocess_engine.py`

## Audit Trail

- EXTRACTED: 101 (99%)
- INFERRED: 1 (1%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*