# Terminal Status Aggregation

> 40 nodes · cohesion 0.08

## Key Concepts

- **test_lifecycle_states.py** (46 connections) — `core/tests/test_lifecycle_states.py`
- **WorkerNetworkError** (24 connections) — `core/gherkai_core/errors.py`
- **_NetRaiseEngine** (20 connections) — `core/tests/test_lifecycle_states.py`
- **_AbortProbeEngine** (18 connections) — `core/tests/test_lifecycle_states.py`
- **_aggregate()** (12 connections) — `core/gherkai_core/project.py`
- **fake_engine.py** (12 connections) — `core/tests/fake_engine.py`
- **FakeWorkerHandle** (12 connections) — `core/tests/fake_engine.py`
- **severity()** (7 connections) — `core/gherkai_core/model.py`
- **._gen()** (6 connections) — `core/tests/fake_engine.py`
- **.run_scope()** (5 connections) — `core/tests/fake_engine.py`
- **._gen()** (5 connections) — `core/tests/test_lifecycle_states.py`
- **Event** (4 connections)
- **.__init__()** (3 connections) — `core/tests/fake_engine.py`
- **Job** (3 connections)
- **.run_scope()** (3 connections) — `core/tests/test_lifecycle_states.py`
- **.run_scope()** (3 connections) — `core/tests/test_lifecycle_states.py`
- **.__call__()** (2 connections) — `core/tests/fake_engine.py`
- **.__init__()** (2 connections) — `core/tests/test_lifecycle_states.py`
- **test_aggregate_all_skipped_no_error_not_misjudged_passed()** (2 connections) — `core/tests/test_lifecycle_states.py`
- **test_aggregate_filters_non_verdict()** (2 connections) — `core/tests/test_lifecycle_states.py`
- **test_aggregate_running_does_not_pollute_clean_pass()** (2 connections) — `core/tests/test_lifecycle_states.py`
- **test_pending_running_have_no_severity()** (2 connections) — `core/tests/test_lifecycle_states.py`
- **test_severity_full_chain()** (2 connections) — `core/tests/test_lifecycle_states.py`
- **test_severity_order_fixes_string_sort_trap()** (2 connections) — `core/tests/test_lifecycle_states.py`
- **RuntimeError** (1 connections)
- *... and 15 more nodes in this community*

## Relationships

- [Run Schedule Orchestration](Run_Schedule_Orchestration.md) (37 shared connections)
- [Run Result Verdict Model](Run_Result_Verdict_Model.md) (14 shared connections)
- [Engine Ports & Adapters](Engine_Ports_%26_Adapters.md) (14 shared connections)
- [Event Formatting & Cost Model](Event_Formatting_%26_Cost_Model.md) (11 shared connections)
- [SQLite Event Log & Projection](SQLite_Event_Log_%26_Projection.md) (8 shared connections)
- [ResultStore Local/S3](ResultStore_Local-S3.md) (4 shared connections)
- [Subprocess Engine Integration](Subprocess_Engine_Integration.md) (2 shared connections)
- [Worker Exit Code Translation](Worker_Exit_Code_Translation.md) (1 shared connections)
- [Fargate Engine Unit Tests](Fargate_Engine_Unit_Tests.md) (1 shared connections)
- [Wire Protocol Serialization](Wire_Protocol_Serialization.md) (1 shared connections)

## Source Files

- `core/gherkai_core/errors.py`
- `core/gherkai_core/model.py`
- `core/gherkai_core/project.py`
- `core/tests/fake_engine.py`
- `core/tests/test_lifecycle_states.py`

## Audit Trail

- EXTRACTED: 115 (75%)
- INFERRED: 39 (25%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*