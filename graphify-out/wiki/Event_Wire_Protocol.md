# Event Wire Protocol

> 36 nodes · cohesion 0.08

## Key Concepts

- **test_wire.py** (37 connections) — `core/tests/test_wire.py`
- **event_from_json()** (29 connections) — `core/gherkai_core/wire.py`
- **event_from_line()** (16 connections) — `core/gherkai_core/wire.py`
- **raise_for_worker_exit()** (12 connections) — `core/gherkai_core/wire.py`
- **.records()** (7 connections) — `core/gherkai_core/adapters/event_log/ddb.py`
- **.records()** (6 connections) — `core/gherkai_core/adapters/event_log/sqlite.py`
- **._emit_ts()** (3 connections) — `core/gherkai_core/adapters/event_log/ddb.py`
- **_report_refs_from_json()** (3 connections) — `core/gherkai_core/wire.py`
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
- *... and 11 more nodes in this community*

## Relationships

- [Cloud Adapter Boundary Modules](Cloud_Adapter_Boundary_Modules.md) (19 shared connections)
- [Run Scheduling Events Core](Run_Scheduling_Events_Core.md) (7 shared connections)
- [Subprocess Engine Adapter](Subprocess_Engine_Adapter.md) (7 shared connections)
- [Job Explain Data Model](Job_Explain_Data_Model.md) (6 shared connections)
- [Reconciler Event Projection](Reconciler_Event_Projection.md) (3 shared connections)
- [Fargate Engine Adapter](Fargate_Engine_Adapter.md) (3 shared connections)
- [Cloud Launcher Reconcile Tests](Cloud_Launcher_Reconcile_Tests.md) (2 shared connections)
- [SQLite Event Log](SQLite_Event_Log.md) (2 shared connections)
- [Terminal State Aggregation](Terminal_State_Aggregation.md) (2 shared connections)
- [Fargate Engine Tests](Fargate_Engine_Tests.md) (2 shared connections)
- [Event Exit Records & Keys](Event_Exit_Records_%26_Keys.md) (1 shared connections)
- [Event Progress Formatting](Event_Progress_Formatting.md) (1 shared connections)

## Source Files

- `core/gherkai_core/adapters/event_log/ddb.py`
- `core/gherkai_core/adapters/event_log/sqlite.py`
- `core/gherkai_core/wire.py`
- `core/tests/test_wire.py`

## Audit Trail

- EXTRACTED: 108 (99%)
- INFERRED: 1 (1%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*