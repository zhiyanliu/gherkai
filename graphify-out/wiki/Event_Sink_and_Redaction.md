# Event Sink and Redaction

> 37 nodes · cohesion 0.07

## Key Concepts

- **test_event_sink.py** (14 connections) — `engines/novaact/tests/test_event_sink.py`
- **redact_url_userinfo()** (13 connections) — `engines/novaact/gherkai_worker_novaact/lib/redact.py`
- **EventSink** (10 connections) — `engines/novaact/gherkai_worker_novaact/lib/event_sink.py`
- **novaact/tests/test_redact.py** (8 connections) — `engines/novaact/tests/test_redact.py`
- **event_sink.py** (6 connections) — `engines/novaact/gherkai_worker_novaact/lib/event_sink.py`
- **lib/redact.py** (6 connections) — `engines/novaact/gherkai_worker_novaact/lib/redact.py`
- **.emit()** (4 connections) — `engines/novaact/gherkai_worker_novaact/lib/event_sink.py`
- **._ddb()** (3 connections) — `engines/novaact/gherkai_worker_novaact/lib/event_sink.py`
- **test_json_field_boundary_is_not_crossed()** (3 connections) — `engines/novaact/tests/test_redact.py`
- **test_redact_url_userinfo_cases()** (3 connections) — `engines/novaact/tests/test_redact.py`
- **test_serialized_json_line_stays_valid_and_loses_credentials()** (3 connections) — `engines/novaact/tests/test_redact.py`
- **.__init__()** (2 connections) — `engines/novaact/gherkai_worker_novaact/lib/event_sink.py`
- **test_ddb_mode_missing_run_or_scope_id_fails_loud()** (2 connections) — `engines/novaact/tests/test_event_sink.py`
- **test_emit_flushes_each_event()** (2 connections) — `engines/novaact/tests/test_event_sink.py`
- **test_none_passes_through()** (2 connections) — `engines/novaact/tests/test_redact.py`
- **事件 sink（Nova worker，ADR 0024「I/O 边缘可注入接口」）：worker 主流程唯一的事件出口。 对称 Midscene 的…** (1 connections) — `engines/novaact/gherkai_worker_novaact/lib/event_sink.py`
- **按注入的 env 把 ADR 0024 事件写到事件通道。fd 态：写 EVENTS_FD fd；DDB 态：PutItem 到 events 表。…** (1 connections) — `engines/novaact/gherkai_worker_novaact/lib/event_sink.py`
- **吐一条 ADR 0024 事件（JSON Lines，字段名 camelCase 与 core/gherkai_core/wire.py 一致）。 fd…** (1 connections) — `engines/novaact/gherkai_worker_novaact/lib/event_sink.py`
- **隧道凭据脱敏（ADR 0035 决策 5）：把文本里 `scheme://用户:口令@主机` 的 userinfo 段换成 `***`。 与…** (1 connections) — `engines/novaact/gherkai_worker_novaact/lib/redact.py`
- **`https://u:p@host/x` → `https://***@host/x`；None 原样返回。** (1 connections) — `engines/novaact/gherkai_worker_novaact/lib/redact.py`
- **EventSink 单测（Nova，ADR 0024「I/O 边缘可注入接口」）：subprocess 态写 EVENTS_FD fd + 回落 + 保序 +…** (1 connections) — `engines/novaact/tests/test_event_sink.py`
- **DDB 态缺 RUN_ID/SCOPE_ID → 装配错误 fail-loud(否则事件静默写进 "None#None" 假 PK,run 永不收敛)。** (1 connections) — `engines/novaact/tests/test_event_sink.py`
- **test_ddb_state_binds_target_table_name()** (1 connections) — `engines/novaact/tests/test_event_sink.py`
- **test_ddb_state_putitem()** (1 connections) — `engines/novaact/tests/test_event_sink.py`
- **test_emit_masks_tunnel_credentials_in_serialized_line()** (1 connections) — `engines/novaact/tests/test_event_sink.py`
- *... and 12 more nodes in this community*

## Relationships

- [Nova Act Worker](Nova_Act_Worker.md) (4 shared connections)
- [Step Evidence Records](Step_Evidence_Records.md) (3 shared connections)
- [Release Notes Tooling](Release_Notes_Tooling.md) (1 shared connections)
- [Job Source Input](Job_Source_Input.md) (1 shared connections)
- [Cloud Resource Resolution](Cloud_Resource_Resolution.md) (1 shared connections)
- [Evidence Upload Tests](Evidence_Upload_Tests.md) (1 shared connections)

## Source Files

- `engines/novaact/gherkai_worker_novaact/lib/event_sink.py`
- `engines/novaact/gherkai_worker_novaact/lib/redact.py`
- `engines/novaact/tests/test_event_sink.py`
- `engines/novaact/tests/test_redact.py`

## Audit Trail

- EXTRACTED: 55 (96%)
- INFERRED: 2 (4%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*