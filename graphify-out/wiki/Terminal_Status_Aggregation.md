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

- [Run Scheduling Engine](Run_Scheduling_Engine.md) (37 shared connections)
- [Run Result Rendering](Run_Result_Rendering.md) (12 shared connections)
- [Engine Ports & Adapters](Engine_Ports_%26_Adapters.md) (12 shared connections)
- [Event Progress Formatting](Event_Progress_Formatting.md) (12 shared connections)
- [Boto Guard & S3 Offload](Boto_Guard_%26_S3_Offload.md) (5 shared connections)
- [S3 Result Store](S3_Result_Store.md) (4 shared connections)
- [State Projection & Planning](State_Projection_%26_Planning.md) (4 shared connections)
- [Subprocess Engine Tests](Subprocess_Engine_Tests.md) (2 shared connections)
- [Worker Exit Code Mapping](Worker_Exit_Code_Mapping.md) (1 shared connections)
- [Fargate Engine Tests](Fargate_Engine_Tests.md) (1 shared connections)
- [Fargate Worker Handle](Fargate_Worker_Handle.md) (1 shared connections)
- [Exit Code Await Polling](Exit_Code_Await_Polling.md) (1 shared connections)

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