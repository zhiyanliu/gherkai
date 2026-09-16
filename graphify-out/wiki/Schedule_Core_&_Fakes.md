# Schedule Core & Fakes

> 66 nodes · cohesion 0.17

## Key Concepts

- **test_schedule.py** (72 connections) — `core/tests/test_schedule.py`
- **schedule()** (63 connections) — `core/gherkai_core/schedule.py`
- **CollectSink** (60 connections) — `core/tests/fake_engine.py`
- **FakeEngine** (56 connections) — `core/tests/fake_engine.py`
- **FakeResolver** (53 connections) — `core/tests/fake_engine.py`
- **_job()** (49 connections) — `core/tests/test_schedule.py`
- **_rm()** (48 connections) — `core/tests/test_schedule.py`
- **ScheduleOpts** (47 connections) — `core/gherkai_core/schedule.py`
- **Votes** (32 connections) — `core/gherkai_core/model.py`
- **_passing_events()** (31 connections) — `core/tests/test_schedule.py`
- **_IncClock** (28 connections) — `core/tests/test_schedule.py`
- **test_abort_then_clean_eof_is_aborted_not_passed()** (15 connections) — `core/tests/test_schedule.py`
- **test_fail_fast_batch_errors()** (14 connections) — `core/tests/test_schedule.py`
- **test_failed_and_error_steps_cost_still_aggregated()** (12 connections) — `core/tests/test_schedule.py`
- **test_partial_completion_without_scope_done_not_passed()** (12 connections) — `core/tests/test_schedule.py`
- **test_scope_report_refs_reduced()** (12 connections) — `core/tests/test_schedule.py`
- **test_step_report_refs_reduced()** (12 connections) — `core/tests/test_schedule.py`
- **test_timeout_with_fake_clock()** (12 connections) — `core/tests/test_schedule.py`
- **test_network_error_not_retried_when_session_started()** (11 connections) — `core/tests/test_schedule.py`
- **test_on_job_complete_exception_stops_inflight_workers_before_raise()** (11 connections) — `core/tests/test_schedule.py`
- **test_durations_none_without_started_events()** (10 connections) — `core/tests/test_schedule.py`
- **test_network_retry_deadline_not_reset_across_attempts()** (10 connections) — `core/tests/test_schedule.py`
- **test_on_job_complete_fires_once_per_job_with_final_jobresult()** (10 connections) — `core/tests/test_schedule.py`
- **test_three_level_durations()** (10 connections) — `core/tests/test_schedule.py`
- **test_fail_fast_queued_job_is_skipped()** (9 connections) — `core/tests/test_lifecycle_states.py`
- *... and 41 more nodes in this community*

## Relationships

- [Event Formatting](Event_Formatting.md) (91 shared connections)
- [Typed Errors & Severity](Typed_Errors_%26_Severity.md) (35 shared connections)
- [Cloud Boto3 Guards & EventLog](Cloud_Boto3_Guards_%26_EventLog.md) (18 shared connections)
- [Job Explain & S3 Offload](Job_Explain_%26_S3_Offload.md) (18 shared connections)
- [Subprocess Engine Tests](Subprocess_Engine_Tests.md) (16 shared connections)
- [Local Report Store](Local_Report_Store.md) (6 shared connections)
- [Text Render & Wording Guards](Text_Render_%26_Wording_Guards.md) (3 shared connections)
- [DynamoDB RunStore Adapter](DynamoDB_RunStore_Adapter.md) (3 shared connections)
- [Local Result Store & Persistence](Local_Result_Store_%26_Persistence.md) (3 shared connections)
- [Job Execution with Retry](Job_Execution_with_Retry.md) (3 shared connections)
- [Explain Command Tests](Explain_Command_Tests.md) (2 shared connections)
- [S3 Result Store](S3_Result_Store.md) (2 shared connections)

## Source Files

- `core/gherkai_core/model.py`
- `core/gherkai_core/schedule.py`
- `core/tests/fake_engine.py`
- `core/tests/test_lifecycle_states.py`
- `core/tests/test_schedule.py`

## Audit Trail

- EXTRACTED: 518 (91%)
- INFERRED: 52 (9%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*