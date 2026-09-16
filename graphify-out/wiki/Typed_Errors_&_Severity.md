# Typed Errors & Severity

> 40 nodes · cohesion 0.08

## Key Concepts

- **test_lifecycle_states.py** (46 connections) — `core/tests/test_lifecycle_states.py`
- **WorkerNetworkError** (26 connections) — `core/gherkai_core/errors.py`
- **_NetRaiseEngine** (20 connections) — `core/tests/test_lifecycle_states.py`
- **_aggregate()** (12 connections) — `core/gherkai_core/project.py`
- **fake_engine.py** (12 connections) — `core/tests/fake_engine.py`
- **FakeWorkerHandle** (12 connections) — `core/tests/fake_engine.py`
- **errors.py** (10 connections) — `core/gherkai_core/errors.py`
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

- [Schedule Core & Fakes](Schedule_Core_%26_Fakes.md) (35 shared connections)
- [Cloud Boto3 Guards & EventLog](Cloud_Boto3_Guards_%26_EventLog.md) (16 shared connections)
- [Event Formatting](Event_Formatting.md) (10 shared connections)
- [Run State Projection](Run_State_Projection.md) (5 shared connections)
- [Fargate Worker Handle](Fargate_Worker_Handle.md) (4 shared connections)
- [Job Explain & S3 Offload](Job_Explain_%26_S3_Offload.md) (4 shared connections)
- [S3 Result Store](S3_Result_Store.md) (4 shared connections)
- [Scope Parsing & Plan Errors](Scope_Parsing_%26_Plan_Errors.md) (2 shared connections)
- [Fargate Engine Tests](Fargate_Engine_Tests.md) (2 shared connections)
- [Subprocess Engine Tests](Subprocess_Engine_Tests.md) (2 shared connections)
- [Job Execution with Retry](Job_Execution_with_Retry.md) (2 shared connections)
- [DynamoDB RunStore Adapter](DynamoDB_RunStore_Adapter.md) (2 shared connections)

## Source Files

- `core/gherkai_core/errors.py`
- `core/gherkai_core/model.py`
- `core/gherkai_core/project.py`
- `core/tests/fake_engine.py`
- `core/tests/test_lifecycle_states.py`

## Audit Trail

- EXTRACTED: 119 (80%)
- INFERRED: 30 (20%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*