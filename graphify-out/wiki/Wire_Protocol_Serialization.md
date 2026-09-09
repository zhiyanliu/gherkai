# Wire Protocol Serialization

> 21 nodes · cohesion 0.14

## Key Concepts

- **test_wire.py** (35 connections) — `core/tests/test_wire.py`
- **event_from_json()** (27 connections) — `core/gherkai_core/wire.py`
- **_cost_from_json()** (3 connections) — `core/gherkai_core/wire.py`
- **_report_refs_from_json()** (3 connections) — `core/gherkai_core/wire.py`
- **_votes_from_json()** (3 connections) — `core/gherkai_core/wire.py`
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
- **test_unknown_event_type_raises()** (2 connections) — `core/tests/test_wire.py`
- **JSON dict（worker 事件通道一行）→ model.Event，按 "type" 分派（ADR 0024）。 事件通道随形态而异：子进程态 =…** (1 connections) — `core/gherkai_core/wire.py`
- **wire 协议测试（ADR 0024）：Job 序列化 + 事件反序列化的形状契约。** (1 connections) — `core/tests/test_wire.py`
- **80 是跨语言约定值（两个引擎 worker 各自硬编码）——改这个数即改协议，须同步两 worker。** (1 connections) — `core/tests/test_wire.py`

## Relationships

- [Engine Ports & Adapters](Engine_Ports_%26_Adapters.md) (16 shared connections)
- [Event Formatting & Cost Model](Event_Formatting_%26_Cost_Model.md) (10 shared connections)
- [SQLite Event Log & Projection](SQLite_Event_Log_%26_Projection.md) (4 shared connections)
- [Worker Exit Code Translation](Worker_Exit_Code_Translation.md) (3 shared connections)
- [Run Result Verdict Model](Run_Result_Verdict_Model.md) (2 shared connections)
- [Job Serialization & E2E Harness](Job_Serialization_%26_E2E_Harness.md) (2 shared connections)
- [Environment and Version Resolution](Environment_and_Version_Resolution.md) (1 shared connections)
- [Render & ReportStore Local](Render_%26_ReportStore_Local.md) (1 shared connections)
- [Terminal Status Aggregation](Terminal_Status_Aggregation.md) (1 shared connections)

## Source Files

- `core/gherkai_core/wire.py`
- `core/tests/test_wire.py`

## Audit Trail

- EXTRACTED: 69 (99%)
- INFERRED: 1 (1%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*