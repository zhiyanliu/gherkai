# Run Scheduling Core

> 60 nodes · cohesion 0.20

## Key Concepts

- **test_schedule.py** (72 connections) — `core/tests/test_schedule.py`
- **schedule()** (63 connections) — `core/gherkai_core/schedule.py`
- **CollectSink** (60 connections) — `core/tests/fake_engine.py`
- **FakeEngine** (56 connections) — `core/tests/fake_engine.py`
- **FakeResolver** (53 connections) — `core/tests/fake_engine.py`
- **_job()** (49 connections) — `core/tests/test_schedule.py`
- **_rm()** (48 connections) — `core/tests/test_schedule.py`
- **ScheduleOpts** (47 connections) — `core/gherkai_core/schedule.py`
- **_passing_events()** (31 connections) — `core/tests/test_schedule.py`
- **test_abort_then_clean_eof_is_aborted_not_passed()** (15 connections) — `core/tests/test_schedule.py`
- **test_fail_fast_batch_errors()** (14 connections) — `core/tests/test_schedule.py`
- **test_step_skipped_reduced_to_skipped_shortcircuited()** (13 connections) — `core/tests/test_schedule.py`
- **test_scope_report_refs_reduced()** (12 connections) — `core/tests/test_schedule.py`
- **test_step_report_refs_reduced()** (12 connections) — `core/tests/test_schedule.py`
- **test_step_skipped_does_not_pollute_scenario_or_run_status()** (12 connections) — `core/tests/test_schedule.py`
- **test_step_skipped_without_scenario_done_still_recorded()** (12 connections) — `core/tests/test_schedule.py`
- **test_timeout_with_fake_clock()** (12 connections) — `core/tests/test_schedule.py`
- **test_network_error_not_retried_when_session_started()** (11 connections) — `core/tests/test_schedule.py`
- **test_on_job_complete_exception_stops_inflight_workers_before_raise()** (11 connections) — `core/tests/test_schedule.py`
- **test_durations_none_without_started_events()** (10 connections) — `core/tests/test_schedule.py`
- **test_network_retry_deadline_not_reset_across_attempts()** (10 connections) — `core/tests/test_schedule.py`
- **test_on_job_complete_fires_once_per_job_with_final_jobresult()** (10 connections) — `core/tests/test_schedule.py`
- **test_three_level_durations()** (10 connections) — `core/tests/test_schedule.py`
- **test_fail_fast_queued_job_is_skipped()** (9 connections) — `core/tests/test_lifecycle_states.py`
- **test_network_error_during_timeout_is_timeout_not_aborted()** (9 connections) — `core/tests/test_lifecycle_states.py`
- *... and 35 more nodes in this community*

## Relationships

- [Event Formatting](Event_Formatting.md) (82 shared connections)
- [Event Log Adapters](Event_Log_Adapters.md) (20 shared connections)
- [Subprocess Engine Adapter Tests](Subprocess_Engine_Adapter_Tests.md) (16 shared connections)
- [Job Domain Models](Job_Domain_Models.md) (15 shared connections)
- [Job Status Severity Aggregation](Job_Status_Severity_Aggregation.md) (14 shared connections)
- [Run Result Aggregation Tree](Run_Result_Aggregation_Tree.md) (10 shared connections)
- [Fake Worker Test Doubles](Fake_Worker_Test_Doubles.md) (10 shared connections)
- [Typed Errors and Wire Protocol](Typed_Errors_and_Wire_Protocol.md) (8 shared connections)
- [Job Worker Execution](Job_Worker_Execution.md) (3 shared connections)
- [Result Store & Report Refs](Result_Store_%26_Report_Refs.md) (3 shared connections)
- [Local Result Store](Local_Result_Store.md) (2 shared connections)
- [Release Notes Tooling](Release_Notes_Tooling.md) (1 shared connections)

## Source Files

- `core/gherkai_core/schedule.py`
- `core/tests/fake_engine.py`
- `core/tests/test_lifecycle_states.py`
- `core/tests/test_schedule.py`

## Audit Trail

- EXTRACTED: 500 (93%)
- INFERRED: 35 (7%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*