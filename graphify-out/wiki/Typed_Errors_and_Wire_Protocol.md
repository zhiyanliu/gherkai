# Typed Errors and Wire Protocol

> 53 nodes · cohesion 0.06

## Key Concepts

- **wire.py** (38 connections) — `core/gherkai_core/wire.py`
- **test_wire.py** (37 connections) — `core/tests/test_wire.py`
- **event_from_json()** (29 connections) — `core/gherkai_core/wire.py`
- **WorkerNetworkError** (26 connections) — `core/gherkai_core/errors.py`
- **event_from_line()** (16 connections) — `core/gherkai_core/wire.py`
- **raise_for_worker_exit()** (12 connections) — `core/gherkai_core/wire.py`
- **fake_engine.py** (12 connections) — `core/tests/fake_engine.py`
- **errors.py** (11 connections) — `core/gherkai_core/errors.py`
- **job_to_json()** (9 connections) — `core/gherkai_core/wire.py`
- **job_to_line()** (9 connections) — `core/gherkai_core/wire.py`
- **_scenario_to_json()** (4 connections) — `core/gherkai_core/wire.py`
- **_step_to_json()** (4 connections) — `core/gherkai_core/wire.py`
- **_argument_to_json()** (3 connections) — `core/gherkai_core/wire.py`
- **_cost_from_json()** (3 connections) — `core/gherkai_core/wire.py`
- **_report_refs_from_json()** (3 connections) — `core/gherkai_core/wire.py`
- **_votes_from_json()** (3 connections) — `core/gherkai_core/wire.py`
- **test_job_to_json_assertion_votes_passthrough()** (3 connections) — `core/tests/test_wire.py`
- **test_raise_for_worker_exit_label_names_the_transport_field()** (3 connections) — `core/tests/test_wire.py`
- **test_raise_for_worker_exit_maps_codes()** (3 connections) — `core/tests/test_wire.py`
- **test_step_done_message_masks_tunnel_credentials()** (3 connections) — `core/tests/test_wire.py`
- **Event** (2 connections)
- **Job** (2 connections)
- **test_event_from_line()** (2 connections) — `core/tests/test_wire.py`
- **test_event_scenario_started()** (2 connections) — `core/tests/test_wire.py`
- **test_event_scope_done()** (2 connections) — `core/tests/test_wire.py`
- *... and 28 more nodes in this community*

## Relationships

- [Job Domain Models](Job_Domain_Models.md) (25 shared connections)
- [Event Log Adapters](Event_Log_Adapters.md) (14 shared connections)
- [Event Formatting](Event_Formatting.md) (14 shared connections)
- [Run Scheduling Core](Run_Scheduling_Core.md) (8 shared connections)
- [Run Result Aggregation Tree](Run_Result_Aggregation_Tree.md) (5 shared connections)
- [Fake Worker Test Doubles](Fake_Worker_Test_Doubles.md) (5 shared connections)
- [Fargate Engine Tests](Fargate_Engine_Tests.md) (4 shared connections)
- [Fargate Engine Adapter](Fargate_Engine_Adapter.md) (4 shared connections)
- [Job Status Severity Aggregation](Job_Status_Severity_Aggregation.md) (3 shared connections)
- [Log Pump and Redaction](Log_Pump_and_Redaction.md) (3 shared connections)
- [Subprocess Worker Handle](Subprocess_Worker_Handle.md) (3 shared connections)
- [Scope Tag Grouping](Scope_Tag_Grouping.md) (2 shared connections)

## Source Files

- `core/gherkai_core/errors.py`
- `core/gherkai_core/wire.py`
- `core/tests/fake_engine.py`
- `core/tests/test_wire.py`

## Audit Trail

- EXTRACTED: 179 (93%)
- INFERRED: 14 (7%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*