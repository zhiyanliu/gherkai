# Worker Event Sink & Redaction

> 41 nodes · cohesion 0.06

## Key Concepts

- **test_event_sink.py** (14 connections) — `engines/novaact/tests/test_event_sink.py`
- **redact_url_userinfo()** (13 connections) — `engines/novaact/gherkai_worker_novaact/lib/redact.py`
- **EventSink** (10 connections) — `engines/novaact/gherkai_worker_novaact/lib/event_sink.py`
- **_DeterministicCtx** (9 connections) — `engines/novaact/gherkai_worker_novaact/run_scope.py`
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
- **.__init__()** (1 connections) — `engines/novaact/gherkai_worker_novaact/run_scope.py`
- **.page()** (1 connections) — `engines/novaact/gherkai_worker_novaact/run_scope.py`
- **传给确定性 handler 的上下文：暴露 Playwright `page`（精确 DOM/URL 查，不走 AI）。 Nova 把底层…** (1 connections) — `engines/novaact/gherkai_worker_novaact/run_scope.py`
- **EventSink 单测（Nova，ADR 0024「I/O 边缘可注入接口」）：subprocess 态写 EVENTS_FD fd + 回落 + 保序 +…** (1 connections) — `engines/novaact/tests/test_event_sink.py`
- *... and 16 more nodes in this community*

## Relationships

- [Nova Act Worker Entry](Nova_Act_Worker_Entry.md) (5 shared connections)
- [Step Evidence Records](Step_Evidence_Records.md) (3 shared connections)
- [Worker Job Source Input](Worker_Job_Source_Input.md) (2 shared connections)
- [AWS Target & Network Resolution](AWS_Target_%26_Network_Resolution.md) (1 shared connections)
- [Scenario Evidence Tests](Scenario_Evidence_Tests.md) (1 shared connections)
- [Step Execution & Error Classification](Step_Execution_%26_Error_Classification.md) (1 shared connections)
- [Artifact Uploader](Artifact_Uploader.md) (1 shared connections)
- [Deterministic Step Loading](Deterministic_Step_Loading.md) (1 shared connections)

## Source Files

- `engines/novaact/gherkai_worker_novaact/lib/event_sink.py`
- `engines/novaact/gherkai_worker_novaact/lib/redact.py`
- `engines/novaact/gherkai_worker_novaact/run_scope.py`
- `engines/novaact/tests/test_event_sink.py`
- `engines/novaact/tests/test_redact.py`

## Audit Trail

- EXTRACTED: 60 (92%)
- INFERRED: 5 (8%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*