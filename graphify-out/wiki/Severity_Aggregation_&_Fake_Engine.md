# Severity Aggregation & Fake Engine

> 37 nodes · cohesion 0.08

## Key Concepts

- **test_lifecycle_states.py** (46 connections) — `core/tests/test_lifecycle_states.py`
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
- **终态的 severity 数值（ADR 0031）。前置态 pending/running 无 severity，调用即编程错误。** (1 connections) — `core/gherkai_core/model.py`
- **终态归约（唯一一份，schedule 与本模块两路径共用——ADR 0031 决定三 / 0034「不复制归约逻辑」）： 滤非终态判定后，任一…** (1 connections) — `core/gherkai_core/project.py`
- *... and 12 more nodes in this community*

## Relationships

- [Schedule Module Tests](Schedule_Module_Tests.md) (33 shared connections)
- [Cloud Launcher & Fargate Adapters](Cloud_Launcher_%26_Fargate_Adapters.md) (12 shared connections)
- [Job/Scenario Explain Model](Job-Scenario_Explain_Model.md) (12 shared connections)
- [Event Progress Formatting](Event_Progress_Formatting.md) (11 shared connections)
- [Fake DDB Table & SQLite Records](Fake_DDB_Table_%26_SQLite_Records.md) (7 shared connections)
- [S3 Result Store](S3_Result_Store.md) (7 shared connections)
- [Feature Parsing & Errors](Feature_Parsing_%26_Errors.md) (2 shared connections)
- [Subprocess Engine Logging](Subprocess_Engine_Logging.md) (1 shared connections)

## Source Files

- `core/gherkai_core/model.py`
- `core/gherkai_core/project.py`
- `core/tests/fake_engine.py`
- `core/tests/test_lifecycle_states.py`

## Audit Trail

- EXTRACTED: 106 (77%)
- INFERRED: 31 (23%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*