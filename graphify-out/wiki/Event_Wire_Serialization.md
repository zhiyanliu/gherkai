# Event Wire Serialization

> 48 nodes · cohesion 0.07

## Key Concepts

- **wire.py** (39 connections) — `core/gherkai_core/wire.py`
- **test_wire.py** (37 connections) — `core/tests/test_wire.py`
- **event_from_json()** (29 connections) — `core/gherkai_core/wire.py`
- **StepSkipped** (16 connections) — `core/gherkai_core/model.py`
- **event_from_line()** (15 connections) — `core/gherkai_core/wire.py`
- **raise_for_worker_exit()** (11 connections) — `core/gherkai_core/wire.py`
- **job_to_json()** (9 connections) — `core/gherkai_core/wire.py`
- **job_to_line()** (8 connections) — `core/gherkai_core/wire.py`
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
- **test_event_step_done_cost_tokens()** (2 connections) — `core/tests/test_wire.py`
- **test_event_step_done_failed()** (2 connections) — `core/tests/test_wire.py`
- *... and 23 more nodes in this community*

## Relationships

- [Worker Log Event Formatting](Worker_Log_Event_Formatting.md) (24 shared connections)
- [Run Definition Domain Model](Run_Definition_Domain_Model.md) (13 shared connections)
- [Core Adapters Documentation](Core_Adapters_Documentation.md) (10 shared connections)
- [Event Records Projection](Event_Records_Projection.md) (8 shared connections)
- [Result Tree Text Rendering](Result_Tree_Text_Rendering.md) (6 shared connections)
- [Fargate Engine Adapter](Fargate_Engine_Adapter.md) (4 shared connections)
- [Explain Dict and Redaction](Explain_Dict_and_Redaction.md) (3 shared connections)
- [Subprocess Worker Handle](Subprocess_Worker_Handle.md) (3 shared connections)
- [Report Store Adapters](Report_Store_Adapters.md) (2 shared connections)
- [Boto3 Adapter Guard](Boto3_Adapter_Guard.md) (2 shared connections)
- [SQLite Event Log](SQLite_Event_Log.md) (2 shared connections)
- [Plan and Scope Seam](Plan_and_Scope_Seam.md) (2 shared connections)

## Source Files

- `core/gherkai_core/model.py`
- `core/gherkai_core/wire.py`
- `core/tests/test_wire.py`

## Audit Trail

- EXTRACTED: 152 (94%)
- INFERRED: 10 (6%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*