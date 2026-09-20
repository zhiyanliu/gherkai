# Wire Protocol Serialization

> 35 nodes · cohesion 0.08

## Key Concepts

- **test_wire.py** (35 connections) — `core/tests/test_wire.py`
- **event_from_json()** (27 connections) — `core/gherkai_core/wire.py`
- **raise_for_worker_exit()** (12 connections) — `core/gherkai_core/wire.py`
- **job_to_json()** (9 connections) — `core/gherkai_core/wire.py`
- **job_to_line()** (9 connections) — `core/gherkai_core/wire.py`
- **_scenario_to_json()** (4 connections) — `core/gherkai_core/wire.py`
- **_step_to_json()** (4 connections) — `core/gherkai_core/wire.py`
- **_argument_to_json()** (3 connections) — `core/gherkai_core/wire.py`
- **_report_refs_from_json()** (3 connections) — `core/gherkai_core/wire.py`
- **test_job_to_json_assertion_votes_passthrough()** (3 connections) — `core/tests/test_wire.py`
- **test_raise_for_worker_exit_label_names_the_transport_field()** (3 connections) — `core/tests/test_wire.py`
- **test_raise_for_worker_exit_maps_codes()** (3 connections) — `core/tests/test_wire.py`
- **Job** (2 connections)
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
- **Scenario** (1 connections)
- *... and 10 more nodes in this community*

## Relationships

- [Event Progress Formatting](Event_Progress_Formatting.md) (21 shared connections)
- [Run Metadata & S3 Offload](Run_Metadata_%26_S3_Offload.md) (9 shared connections)
- [Fargate Engine Adapter](Fargate_Engine_Adapter.md) (6 shared connections)
- [Subprocess Engine Adapter](Subprocess_Engine_Adapter.md) (4 shared connections)
- [Run State Rendering](Run_State_Rendering.md) (3 shared connections)
- [Event Log & Projection](Event_Log_%26_Projection.md) (2 shared connections)
- [DynamoDB Event Log](DynamoDB_Event_Log.md) (2 shared connections)
- [Core Typed Errors](Core_Typed_Errors.md) (2 shared connections)
- [Backend CDK Stack](Backend_CDK_Stack.md) (1 shared connections)
- [End-to-End Test Harness](End-to-End_Test_Harness.md) (1 shared connections)
- [Worker Exit Code Mapping](Worker_Exit_Code_Mapping.md) (1 shared connections)
- [Fargate Engine Tests](Fargate_Engine_Tests.md) (1 shared connections)

## Source Files

- `core/gherkai_core/wire.py`
- `core/tests/test_wire.py`

## Audit Trail

- EXTRACTED: 101 (99%)
- INFERRED: 1 (1%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*