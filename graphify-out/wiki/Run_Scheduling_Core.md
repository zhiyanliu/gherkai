# Run Scheduling Core

> 52 nodes · cohesion 0.22

## Key Concepts

- **test_schedule.py** (72 connections) — `core/tests/test_schedule.py`
- **schedule()** (66 connections) — `core/gherkai_core/schedule.py`
- **CollectSink** (60 connections) — `core/tests/fake_engine.py`
- **FakeEngine** (56 connections) — `core/tests/fake_engine.py`
- **FakeResolver** (53 connections) — `core/tests/fake_engine.py`
- **_job()** (49 connections) — `core/tests/test_schedule.py`
- **_rm()** (48 connections) — `core/tests/test_schedule.py`
- **ScheduleOpts** (47 connections) — `core/gherkai_core/schedule.py`
- **_passing_events()** (31 connections) — `core/tests/test_schedule.py`
- **test_timeout_with_fake_clock()** (12 connections) — `core/tests/test_schedule.py`
- **test_network_error_not_retried_when_session_started()** (11 connections) — `core/tests/test_schedule.py`
- **test_on_job_complete_exception_stops_inflight_workers_before_raise()** (11 connections) — `core/tests/test_schedule.py`
- **test_durations_none_without_started_events()** (10 connections) — `core/tests/test_schedule.py`
- **test_network_retry_deadline_not_reset_across_attempts()** (10 connections) — `core/tests/test_schedule.py`
- **test_on_job_complete_fires_once_per_job_with_final_jobresult()** (10 connections) — `core/tests/test_schedule.py`
- **test_three_level_durations()** (10 connections) — `core/tests/test_schedule.py`
- **test_fail_fast_queued_job_is_skipped()** (9 connections) — `core/tests/test_lifecycle_states.py`
- **test_network_error_during_timeout_is_timeout_not_aborted()** (9 connections) — `core/tests/test_lifecycle_states.py`
- **test_grace_at_or_above_min_grace_ok()** (9 connections) — `core/tests/test_schedule.py`
- **test_grace_below_min_grace_raises()** (9 connections) — `core/tests/test_schedule.py`
- **test_grace_nonpositive_raises()** (9 connections) — `core/tests/test_schedule.py`
- **test_mixed_legs_each_native_metric_aggregated_separately()** (9 connections) — `core/tests/test_schedule.py`
- **test_network_error_exhausted_is_network_error()** (9 connections) — `core/tests/test_schedule.py`
- **test_network_error_retried_then_succeeds()** (9 connections) — `core/tests/test_schedule.py`
- **test_no_fail_fast_lets_others_finish()** (9 connections) — `core/tests/test_schedule.py`
- *... and 27 more nodes in this community*

## Relationships

- [Event Progress Formatting](Event_Progress_Formatting.md) (115 shared connections)
- [Core Typed Errors](Core_Typed_Errors.md) (31 shared connections)
- [Subprocess Engine Tests](Subprocess_Engine_Tests.md) (16 shared connections)
- [Run Metadata & S3 Offload](Run_Metadata_%26_S3_Offload.md) (14 shared connections)
- [S3 Result Store Port](S3_Result_Store_Port.md) (11 shared connections)
- [Event Log & Projection](Event_Log_%26_Projection.md) (4 shared connections)
- [Run State Rendering](Run_State_Rendering.md) (4 shared connections)
- [Job Sink Primitives](Job_Sink_Primitives.md) (2 shared connections)
- [Explain Rendering Tests](Explain_Rendering_Tests.md) (2 shared connections)
- [Backend CDK Stack](Backend_CDK_Stack.md) (1 shared connections)
- [Local Result Store](Local_Result_Store.md) (1 shared connections)
- [Core Package Docs](Core_Package_Docs.md) (1 shared connections)

## Source Files

- `core/gherkai_core/schedule.py`
- `core/tests/fake_engine.py`
- `core/tests/test_lifecycle_states.py`
- `core/tests/test_schedule.py`

## Audit Trail

- EXTRACTED: 466 (93%)
- INFERRED: 34 (7%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*