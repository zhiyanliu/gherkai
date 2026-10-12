# Wire Protocol Serialization

> 29 nodes · cohesion 0.11

## Key Concepts

- **test_wire.py** (37 connections) — `core/tests/test_wire.py`
- **event_from_json()** (29 connections) — `core/gherkai_core/wire.py`
- **event_from_line()** (16 connections) — `core/gherkai_core/wire.py`
- **_report_refs_from_json()** (3 connections) — `core/gherkai_core/wire.py`
- **_votes_from_json()** (3 connections) — `core/gherkai_core/wire.py`
- **test_raise_for_worker_exit_label_names_the_transport_field()** (3 connections) — `core/tests/test_wire.py`
- **test_raise_for_worker_exit_maps_codes()** (3 connections) — `core/tests/test_wire.py`
- **test_step_done_message_masks_tunnel_credentials()** (3 connections) — `core/tests/test_wire.py`
- **Event** (2 connections)
- **test_event_from_line()** (2 connections) — `core/tests/test_wire.py`
- **test_event_scenario_started()** (2 connections) — `core/tests/test_wire.py`
- **test_event_scope_done()** (2 connections) — `core/tests/test_wire.py`
- **test_event_step_done_cost_tokens()** (2 connections) — `core/tests/test_wire.py`
- **test_event_step_done_failed()** (2 connections) — `core/tests/test_wire.py`
- **test_event_step_done_no_report_refs_defaults_empty()** (2 connections) — `core/tests/test_wire.py`
- **test_event_step_done_parse_unaffected_by_step_skipped()** (2 connections) — `core/tests/test_wire.py`
- **test_event_step_done_with_report_refs()** (2 connections) — `core/tests/test_wire.py`
- **test_event_step_done_with_votes_and_cost()** (2 connections) — `core/tests/test_wire.py`
- **test_event_step_skipped()** (2 connections) — `core/tests/test_wire.py`
- **test_ex_worker_network_value_is_protocol_pinned()** (2 connections) — `core/tests/test_wire.py`
- **test_step_done_without_message_stays_none()** (2 connections) — `core/tests/test_wire.py`
- **test_unknown_event_type_raises()** (2 connections) — `core/tests/test_wire.py`
- **JSON dict（worker 事件通道一行）→ model.Event，按 "type" 分派（ADR 0024）。 事件通道随形态而异：子进程态下是专用…** (1 connections) — `core/gherkai_core/wire.py`
- **worker 事件通道一行（子进程态下取 EVENTS_FD 的 fd，Fargate 态下取 DDB events 表 body）→ model.Event。** (1 connections) — `core/gherkai_core/wire.py`
- **wire 协议测试（ADR 0024）：Job 序列化 + 事件反序列化的形状契约。** (1 connections) — `core/tests/test_wire.py`
- *... and 4 more nodes in this community*

## Relationships

- [Job/Scenario Explain Model](Job-Scenario_Explain_Model.md) (15 shared connections)
- [Event Progress Formatting](Event_Progress_Formatting.md) (12 shared connections)
- [Fake DDB Table & SQLite Records](Fake_DDB_Table_%26_SQLite_Records.md) (4 shared connections)
- [Cloud Launcher & Fargate Adapters](Cloud_Launcher_%26_Fargate_Adapters.md) (4 shared connections)
- [Fargate Task Polling](Fargate_Task_Polling.md) (2 shared connections)
- [Job Serialization](Job_Serialization.md) (2 shared connections)
- [Explain JSON & Redaction](Explain_JSON_%26_Redaction.md) (1 shared connections)
- [Worker Job Source Input](Worker_Job_Source_Input.md) (1 shared connections)
- [DynamoDB Event Log](DynamoDB_Event_Log.md) (1 shared connections)
- [Subprocess Worker Handle](Subprocess_Worker_Handle.md) (1 shared connections)
- [Boto3 Guard & Arg Offload](Boto3_Guard_%26_Arg_Offload.md) (1 shared connections)
- [SQLite Event Log Adapter](SQLite_Event_Log_Adapter.md) (1 shared connections)

## Source Files

- `core/gherkai_core/wire.py`
- `core/tests/test_wire.py`

## Audit Trail

- EXTRACTED: 88 (99%)
- INFERRED: 1 (1%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*