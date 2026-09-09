# Scenario

> God node · 62 connections · `core/gherkai_core/model.py`

**Community:** [Engine Ports & Adapters](Engine_Ports_%26_Adapters.md)

## Connections by Relation

### calls
- _job() `EXTRACTED`
- _job() `EXTRACTED`
- _seed_run() `EXTRACTED`
- _meta() `EXTRACTED`
- _job() `EXTRACTED`
- _timeout_built() `EXTRACTED`
- parse_feature() `EXTRACTED`
- _job_def() `EXTRACTED`
- test_offload_unblocks_oversized_docstring_real() `EXTRACTED`
- test_offload_round_trip_real() `EXTRACTED`
- _job() `EXTRACTED`
- test_meta_json_holds_pointers_not_payload() `EXTRACTED`
- test_reader_without_offloader_fails_loud_on_offloaded_meta() `EXTRACTED`
- test_reader_without_offloader_not_fooled_by_content_ref_as_text() `EXTRACTED`
- test_restore_uses_uri_not_current_prefix() `EXTRACTED`
- test_detached_flag_on_state_item() `EXTRACTED`
- test_worker_task_def_arns_on_state_item() `EXTRACTED`
- _job() `EXTRACTED`
- _job() `EXTRACTED`
- test_records_feed_project_to_terminal() `EXTRACTED`

### contains
- model.py `EXTRACTED`

### imports
- test_schedule.py `EXTRACTED`
- test_fargate_engine.py `EXTRACTED`
- test_stores.py `EXTRACTED`
- test_project.py `EXTRACTED`
- serialize.py `EXTRACTED`
- wire.py `EXTRACTED`
- test_cloud_reconcile.py `EXTRACTED`
- test_wire.py `EXTRACTED`
- test_conditional_writes.py `EXTRACTED`
- test_subprocess_engine.py `EXTRACTED`
- test_reconcile.py `EXTRACTED`
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
- _RecorderWatch `INFERRED`
- _FakeEcs `INFERRED`
- _SeqEcs `INFERRED`
- _FakeSchedulerClient `INFERRED`
- _FakeStartEngine `INFERRED`
- _FakeProc `INFERRED`
- ParsedScenario `INFERRED`
- BoomLauncher `INFERRED`
- ConflictException `INFERRED`
- exceptions `INFERRED`

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*