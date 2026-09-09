# Worker Event Sink

> 22 nodes · cohesion 0.10

## Key Concepts

- **test_event_sink.py** (13 connections) — `engines/novaact/tests/test_event_sink.py`
- **EventSink** (10 connections) — `engines/novaact/gherkai_worker_novaact/lib/event_sink.py`
- **event_sink.py** (4 connections) — `engines/novaact/gherkai_worker_novaact/lib/event_sink.py`
- **.emit()** (3 connections) — `engines/novaact/gherkai_worker_novaact/lib/event_sink.py`
- **._ddb()** (2 connections) — `engines/novaact/gherkai_worker_novaact/lib/event_sink.py`
- **.__init__()** (2 connections) — `engines/novaact/gherkai_worker_novaact/lib/event_sink.py`
- **test_ddb_mode_missing_run_or_scope_id_fails_loud()** (2 connections) — `engines/novaact/tests/test_event_sink.py`
- **test_emit_flushes_each_event()** (2 connections) — `engines/novaact/tests/test_event_sink.py`
- **事件 sink（Nova worker，ADR 0024「I/O 边缘可注入接口」）：worker 主流程唯一的事件出口。 对称 Midscene 的…** (1 connections) — `engines/novaact/gherkai_worker_novaact/lib/event_sink.py`
- **按注入的 env 把 ADR 0024 事件写到事件通道。fd 态：写 EVENTS_FD fd；DDB 态：PutItem 到 events 表。…** (1 connections) — `engines/novaact/gherkai_worker_novaact/lib/event_sink.py`
- **吐一条 ADR 0024 事件（JSON Lines，字段名 camelCase 与 core/gherkai_core/wire.py 一致）。 fd…** (1 connections) — `engines/novaact/gherkai_worker_novaact/lib/event_sink.py`
- **EventSink 单测（Nova，ADR 0024「I/O 边缘可注入接口」）：subprocess 态写 EVENTS_FD fd + 回落 + 保序 +…** (1 connections) — `engines/novaact/tests/test_event_sink.py`
- **DDB 态缺 RUN_ID/SCOPE_ID → 装配错误 fail-loud(否则事件静默写进 "None#None" 假 PK,run 永不收敛)。** (1 connections) — `engines/novaact/tests/test_event_sink.py`
- **test_ddb_state_binds_target_table_name()** (1 connections) — `engines/novaact/tests/test_event_sink.py`
- **test_ddb_state_putitem()** (1 connections) — `engines/novaact/tests/test_event_sink.py`
- **test_emit_preserves_chinese_ensure_ascii_false()** (1 connections) — `engines/novaact/tests/test_event_sink.py`
- **test_emit_writes_jsonline_to_injected_fd()** (1 connections) — `engines/novaact/tests/test_event_sink.py`
- **test_empty_ddb_table_treated_as_unset()** (1 connections) — `engines/novaact/tests/test_event_sink.py`
- **test_from_env_falls_back_to_stdout_on_bad_fd_number()** (1 connections) — `engines/novaact/tests/test_event_sink.py`
- **test_from_env_falls_back_to_stdout_on_invalid_events_fd()** (1 connections) — `engines/novaact/tests/test_event_sink.py`
- **test_from_env_falls_back_to_stdout_when_no_events_fd()** (1 connections) — `engines/novaact/tests/test_event_sink.py`
- **TextIO** (1 connections)

## Relationships

- [Nova Act Worker Package](Nova_Act_Worker_Package.md) (2 shared connections)
- [Environment and Version Resolution](Environment_and_Version_Resolution.md) (1 shared connections)
- [Job Source Input](Job_Source_Input.md) (1 shared connections)

## Source Files

- `engines/novaact/gherkai_worker_novaact/lib/event_sink.py`
- `engines/novaact/tests/test_event_sink.py`

## Audit Trail

- EXTRACTED: 27 (96%)
- INFERRED: 1 (4%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*