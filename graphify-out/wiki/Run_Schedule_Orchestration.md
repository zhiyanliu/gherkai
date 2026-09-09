# Run Schedule Orchestration

> 51 nodes · cohesion 0.23

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
- **test_non_network_crash_not_retried()** (9 connections) — `core/tests/test_schedule.py`
- *... and 26 more nodes in this community*

## Relationships

- [Event Formatting & Cost Model](Event_Formatting_%26_Cost_Model.md) (113 shared connections)
- [Terminal Status Aggregation](Terminal_Status_Aggregation.md) (37 shared connections)
- [Run Result Verdict Model](Run_Result_Verdict_Model.md) (16 shared connections)
- [Subprocess Engine Integration](Subprocess_Engine_Integration.md) (16 shared connections)
- [Engine Ports & Adapters](Engine_Ports_%26_Adapters.md) (11 shared connections)
- [Run State Rendering & Boto Guard](Run_State_Rendering_%26_Boto_Guard.md) (4 shared connections)
- [SQLite Event Log & Projection](SQLite_Event_Log_%26_Projection.md) (4 shared connections)
- [Cloud Launcher & DDB EventLog](Cloud_Launcher_%26_DDB_EventLog.md) (2 shared connections)
- [Environment and Version Resolution](Environment_and_Version_Resolution.md) (1 shared connections)
- [Run Persistence Orchestration](Run_Persistence_Orchestration.md) (1 shared connections)
- [Render & ReportStore Local](Render_%26_ReportStore_Local.md) (1 shared connections)

## Source Files

- `core/gherkai_core/schedule.py`
- `core/tests/fake_engine.py`
- `core/tests/test_lifecycle_states.py`
- `core/tests/test_schedule.py`

## Audit Trail

- EXTRACTED: 459 (93%)
- INFERRED: 34 (7%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*