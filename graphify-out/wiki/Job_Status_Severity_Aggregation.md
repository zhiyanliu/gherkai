# Job Status Severity Aggregation

> 17 nodes · cohesion 0.15

## Key Concepts

- **test_lifecycle_states.py** (46 connections) — `core/tests/test_lifecycle_states.py`
- **_aggregate()** (12 connections) — `core/gherkai_core/project.py`
- **severity()** (7 connections) — `core/gherkai_core/model.py`
- **test_aggregate_all_skipped_no_error_not_misjudged_passed()** (2 connections) — `core/tests/test_lifecycle_states.py`
- **test_aggregate_filters_non_verdict()** (2 connections) — `core/tests/test_lifecycle_states.py`
- **test_aggregate_running_does_not_pollute_clean_pass()** (2 connections) — `core/tests/test_lifecycle_states.py`
- **test_pending_running_have_no_severity()** (2 connections) — `core/tests/test_lifecycle_states.py`
- **test_severity_full_chain()** (2 connections) — `core/tests/test_lifecycle_states.py`
- **test_severity_order_fixes_string_sort_trap()** (2 connections) — `core/tests/test_lifecycle_states.py`
- **终态的 severity 数值（ADR 0031）。前置态 pending/running 无 severity，调用即编程错误。** (1 connections) — `core/gherkai_core/model.py`
- **终态归约（唯一一份，schedule 与本模块两路径共用——ADR 0031 决定三 / 0034「不复制归约逻辑」）： 滤非终态判定后，任一…** (1 connections) — `core/gherkai_core/project.py`
- **job 生命周期态 + severity 单测（ADR 0031）：skipped/aborted/pending/running、severity…** (1 connections) — `core/tests/test_lifecycle_states.py`
- **test_non_verdict_filter_set()** (1 connections) — `core/tests/test_lifecycle_states.py`
- **test_severity_skipped_lightest_aborted_heaviest()** (1 connections) — `core/tests/test_lifecycle_states.py`
- **test_terminal_and_non_verdict_are_two_different_cuts()** (1 connections) — `core/tests/test_lifecycle_states.py`
- **test_terminal_statuses_equals_severity_table_keys()** (1 connections) — `core/tests/test_lifecycle_states.py`
- **test_terminal_statuses_is_everything_but_the_two_pre_terminal()** (1 connections) — `core/tests/test_lifecycle_states.py`

## Relationships

- [Run Scheduling Core](Run_Scheduling_Core.md) (14 shared connections)
- [Event Formatting](Event_Formatting.md) (5 shared connections)
- [Run Result Aggregation Tree](Run_Result_Aggregation_Tree.md) (4 shared connections)
- [Event Log Adapters](Event_Log_Adapters.md) (4 shared connections)
- [Cloud Store Adapters](Cloud_Store_Adapters.md) (4 shared connections)
- [Job Domain Models](Job_Domain_Models.md) (3 shared connections)
- [Run State Projection](Run_State_Projection.md) (3 shared connections)
- [Typed Errors and Wire Protocol](Typed_Errors_and_Wire_Protocol.md) (3 shared connections)
- [Fake Worker Test Doubles](Fake_Worker_Test_Doubles.md) (2 shared connections)
- [Job Worker Execution](Job_Worker_Execution.md) (1 shared connections)

## Source Files

- `core/gherkai_core/model.py`
- `core/gherkai_core/project.py`
- `core/tests/test_lifecycle_states.py`

## Audit Trail

- EXTRACTED: 61 (95%)
- INFERRED: 3 (5%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*