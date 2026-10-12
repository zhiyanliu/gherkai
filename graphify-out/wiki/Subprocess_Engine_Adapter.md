# Subprocess Engine Adapter

> 49 nodes · cohesion 0.06

## Key Concepts

- **subprocess_engine.py** (23 connections) — `core/gherkai_core/adapters/subprocess_engine.py`
- **redact_url_userinfo()** (11 connections) — `core/gherkai_core/redact.py`
- **core/tests/test_redact.py** (11 connections) — `core/tests/test_redact.py`
- **_pump_log()** (9 connections) — `core/gherkai_core/adapters/subprocess_engine.py`
- **gherkai_core/redact.py** (9 connections) — `core/gherkai_core/redact.py`
- **job_to_json()** (9 connections) — `core/gherkai_core/wire.py`
- **job_to_line()** (9 connections) — `core/gherkai_core/wire.py`
- **_read_events()** (8 connections) — `core/gherkai_core/adapters/subprocess_engine.py`
- **.run_scope()** (8 connections) — `core/gherkai_core/adapters/subprocess_engine.py`
- **redact_deep()** (8 connections) — `core/gherkai_core/redact.py`
- **SubprocessWorkerHandle** (7 connections) — `core/gherkai_core/adapters/subprocess_engine.py`
- **_scope_color()** (5 connections) — `core/gherkai_core/adapters/subprocess_engine.py`
- **_join_pumps()** (4 connections) — `core/gherkai_core/adapters/subprocess_engine.py`
- **test_json_field_boundary_is_not_crossed()** (3 connections) — `core/tests/test_redact.py`
- **test_redact_url_userinfo_cases()** (3 connections) — `core/tests/test_redact.py`
- **test_serialized_json_line_stays_valid_and_loses_credentials()** (3 connections) — `core/tests/test_redact.py`
- **test_pump_log_masks_tunnel_credentials_in_sink_and_stderr()** (3 connections) — `core/tests/test_subprocess_engine.py`
- **test_job_to_json_assertion_votes_passthrough()** (3 connections) — `core/tests/test_wire.py`
- **Event** (2 connections)
- **Popen** (2 connections)
- **.__init__()** (2 connections) — `core/gherkai_core/adapters/subprocess_engine.py`
- **.stop()** (2 connections) — `core/gherkai_core/adapters/subprocess_engine.py`
- **.wait()** (2 connections) — `core/gherkai_core/adapters/subprocess_engine.py`
- **Job** (2 connections)
- **test_none_passes_through()** (2 connections) — `core/tests/test_redact.py`
- *... and 24 more nodes in this community*

## Relationships

- [Cloud Adapter Boundary Modules](Cloud_Adapter_Boundary_Modules.md) (9 shared connections)
- [Event Wire Protocol](Event_Wire_Protocol.md) (7 shared connections)
- [Job Explain Data Model](Job_Explain_Data_Model.md) (5 shared connections)
- [Subprocess Engine Tests](Subprocess_Engine_Tests.md) (5 shared connections)
- [Terminal Color Policy](Terminal_Color_Policy.md) (3 shared connections)
- [Subprocess Engine & Launcher](Subprocess_Engine_%26_Launcher.md) (2 shared connections)
- [CLI Command Entry Points](CLI_Command_Entry_Points.md) (2 shared connections)
- [SSM Paths And Compose](SSM_Paths_And_Compose.md) (1 shared connections)
- [Detached Local Run Host](Detached_Local_Run_Host.md) (1 shared connections)
- [Detached Launcher Reconcile Loop](Detached_Launcher_Reconcile_Loop.md) (1 shared connections)
- [Color Env Test Isolation](Color_Env_Test_Isolation.md) (1 shared connections)
- [Plan Explain Rendering](Plan_Explain_Rendering.md) (1 shared connections)

## Source Files

- `core/gherkai_core/adapters/subprocess_engine.py`
- `core/gherkai_core/redact.py`
- `core/gherkai_core/wire.py`
- `core/tests/test_redact.py`
- `core/tests/test_subprocess_engine.py`
- `core/tests/test_wire.py`

## Audit Trail

- EXTRACTED: 108 (98%)
- INFERRED: 2 (2%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*