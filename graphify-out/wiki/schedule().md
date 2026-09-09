# schedule()

> God node · 63 connections · `core/gherkai_core/schedule.py`

**Community:** [Run Schedule Orchestration](Run_Schedule_Orchestration.md)

## Connections by Relation

### calls
- _Worker `EXTRACTED`
- ValueError `INFERRED`
- test_abort_then_clean_eof_is_aborted_not_passed() `EXTRACTED`
- test_fail_fast_batch_errors() `EXTRACTED`
- test_step_skipped_reduced_to_skipped_shortcircuited() `EXTRACTED`
- _aggregate() `EXTRACTED`
- test_failed_and_error_steps_cost_still_aggregated() `EXTRACTED`
- test_partial_completion_without_scope_done_not_passed() `EXTRACTED`
- test_scope_report_refs_reduced() `EXTRACTED`
- test_step_report_refs_reduced() `EXTRACTED`
- test_step_skipped_does_not_pollute_scenario_or_run_status() `EXTRACTED`
- test_step_skipped_without_scenario_done_still_recorded() `EXTRACTED`
- test_timeout_with_fake_clock() `EXTRACTED`
- test_network_error_not_retried_when_session_started() `EXTRACTED`
- test_on_job_complete_exception_stops_inflight_workers_before_raise() `EXTRACTED`
- test_durations_none_without_started_events() `EXTRACTED`
- test_network_retry_deadline_not_reset_across_attempts() `EXTRACTED`
- test_on_job_complete_fires_once_per_job_with_final_jobresult() `EXTRACTED`
- test_three_level_durations() `EXTRACTED`
- test_fail_fast_queued_job_is_skipped() `EXTRACTED`

### contains
- schedule.py `EXTRACTED`

### imports
- test_schedule.py `EXTRACTED`
- test_lifecycle_states.py `EXTRACTED`
- test_subprocess_engine.py `EXTRACTED`

### rationale_for
- 跑一次 run（RunMeta = definition）→ RunResult（ADR 0026）。 run_meta: 一次 run 的… `EXTRACTED`

### references
- [RunMeta](RunMeta.md) `EXTRACTED`
- RunResult `EXTRACTED`
- ScheduleOpts `EXTRACTED`
- EngineResolver `EXTRACTED`
- Sink `EXTRACTED`
- JobSink `EXTRACTED`

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*