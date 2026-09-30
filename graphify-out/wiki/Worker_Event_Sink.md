# Worker Event Sink

> 43 nodes · cohesion 0.06

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
- **.from_env()** (3 connections) — `engines/novaact/gherkai_worker_novaact/lib/event_sink.py`
- **test_json_field_boundary_is_not_crossed()** (3 connections) — `engines/novaact/tests/test_redact.py`
- **test_redact_url_userinfo_cases()** (3 connections) — `engines/novaact/tests/test_redact.py`
- **test_serialized_json_line_stays_valid_and_loses_credentials()** (3 connections) — `engines/novaact/tests/test_redact.py`
- **.__init__()** (2 connections) — `engines/novaact/gherkai_worker_novaact/lib/event_sink.py`
- **test_ddb_mode_missing_run_or_scope_id_fails_loud()** (2 connections) — `engines/novaact/tests/test_event_sink.py`
- **test_emit_flushes_each_event()** (2 connections) — `engines/novaact/tests/test_event_sink.py`
- **test_none_passes_through()** (2 connections) — `engines/novaact/tests/test_redact.py`
- **事件 sink（Nova worker，ADR 0024「I/O 边缘可注入接口」）：worker 主流程唯一的事件出口。 对称 Midscene 的…** (1 connections) — `engines/novaact/gherkai_worker_novaact/lib/event_sink.py`
- **按注入的 env 把 ADR 0024 事件写到事件通道。fd 态：写 EVENTS_FD fd；DDB 态：PutItem 到 events 表。…** (1 connections) — `engines/novaact/gherkai_worker_novaact/lib/event_sink.py`
- **从注入的 env 造（唯一读 env 处）。EVENTS_DDB_TABLE 非空 → DDB 态；否则 fd 态（EVENTS_FD 无/非法 → 回落…** (1 connections) — `engines/novaact/gherkai_worker_novaact/lib/event_sink.py`
- **吐一条 ADR 0024 事件（JSON Lines，字段名 camelCase 与 core/gherkai_core/wire.py 一致）。 fd…** (1 connections) — `engines/novaact/gherkai_worker_novaact/lib/event_sink.py`
- **隧道凭据脱敏（ADR 0035 决策 5）：把文本里 `scheme://用户:口令@主机` 的 userinfo 段换成 `***`。 与…** (1 connections) — `engines/novaact/gherkai_worker_novaact/lib/redact.py`
- **`https://u:p@host/x` → `https://***@host/x`；None 原样返回。** (1 connections) — `engines/novaact/gherkai_worker_novaact/lib/redact.py`
- **.__init__()** (1 connections) — `engines/novaact/gherkai_worker_novaact/run_scope.py`
- **.page()** (1 connections) — `engines/novaact/gherkai_worker_novaact/run_scope.py`
- *... and 18 more nodes in this community*

## Relationships

- [Nova Act Worker Runtime](Nova_Act_Worker_Runtime.md) (5 shared connections)
- [CLI Test Fixtures](CLI_Test_Fixtures.md) (3 shared connections)
- [Composition Root Helpers](Composition_Root_Helpers.md) (1 shared connections)
- [Release Notes Rendering](Release_Notes_Rendering.md) (1 shared connections)
- [Single-Line Error Text](Single-Line_Error_Text.md) (1 shared connections)
- [Step and Scenario Execution](Step_and_Scenario_Execution.md) (1 shared connections)
- [Worker Job Source](Worker_Job_Source.md) (1 shared connections)
- [Artifact Uploader (Python)](Artifact_Uploader_%28Python%29.md) (1 shared connections)
- [User Step Loading](User_Step_Loading.md) (1 shared connections)

## Source Files

- `engines/novaact/gherkai_worker_novaact/lib/event_sink.py`
- `engines/novaact/gherkai_worker_novaact/lib/redact.py`
- `engines/novaact/gherkai_worker_novaact/run_scope.py`
- `engines/novaact/tests/test_event_sink.py`
- `engines/novaact/tests/test_redact.py`

## Audit Trail

- EXTRACTED: 61 (91%)
- INFERRED: 6 (9%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*