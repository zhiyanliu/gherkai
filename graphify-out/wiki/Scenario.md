# Scenario

> God node · 73 connections · `core/gherkai_core/model.py`

**Community:** [Job Explain & S3 Offload](Job_Explain_%26_S3_Offload.md)

## Connections by Relation

### calls
- _job() `EXTRACTED`
- _meta() `EXTRACTED`
- _job() `EXTRACTED`
- _seed_run() `EXTRACTED`
- _timeout_built() `EXTRACTED`
- _job() `EXTRACTED`
- parse_feature() `EXTRACTED`
- _job_def() `EXTRACTED`
- _seed_finished_run() `EXTRACTED`
- test_offload_unblocks_oversized_docstring_real() `EXTRACTED`
- test_report_still_written_when_the_run_duration_read_fails() `EXTRACTED`
- test_explain_to_dict_drops_unmatched_scopes_and_keeps_job_fact() `EXTRACTED`
- test_offload_round_trip_real() `EXTRACTED`
- _job() `EXTRACTED`
- test_build_wires_arg_offloader_so_step_argument_bodies_read_back() `EXTRACTED`
- test_detached_flag_on_state_item() `EXTRACTED`
- test_worker_task_def_arns_on_state_item() `EXTRACTED`
- _job() `EXTRACTED`
- test_meta_json_holds_pointers_not_payload() `EXTRACTED`
- test_reader_without_offloader_fails_loud_on_offloaded_meta() `EXTRACTED`

### contains
- model.py `EXTRACTED`

### imports
- test_fargate_engine.py `EXTRACTED`
- test_schedule.py `EXTRACTED`
- test_project.py `EXTRACTED`
- test_stores.py `EXTRACTED`
- serialize.py `EXTRACTED`
- test_cloud_reconcile.py `EXTRACTED`
- wire.py `EXTRACTED`
- test_conditional_writes.py `EXTRACTED`
- test_reconcile.py `EXTRACTED`
- test_wire.py `EXTRACTED`
- test_subprocess_engine.py `EXTRACTED`
- test_cloud_integration.py `EXTRACTED`
- test_ddb_run_store.py `EXTRACTED`
- test_arg_offload.py `EXTRACTED`
- test_sqlite_event_log.py `EXTRACTED`
- parse.py `EXTRACTED`

### rationale_for
- 一个 scenario（Outline 已展开成独立 Scenario，ADR 0025）。 `EXTRACTED`

### uses
- _IncClock `INFERRED`
- _FakeEcs `INFERRED`
- FakeLauncher `INFERRED`
- _MissingThenStoppedEcs `INFERRED`
- _FakeSchedulerClient `INFERRED`
- _RoundsTable `INFERRED`
- _RecorderWatch `INFERRED`
- _FakeEcs `INFERRED`
- _SeqEcs `INFERRED`
- _FakeProc `INFERRED`
- ParsedScenario `INFERRED`
- _FakeStartEngine `INFERRED`
- BoomLauncher `INFERRED`
- _OrderRecordingRunStore `INFERRED`
- _RecordingResultStore `INFERRED`
- ConflictException `INFERRED`
- exceptions `INFERRED`

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*