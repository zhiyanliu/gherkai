# Job

> God node · 117 connections · `core/gherkai_core/model.py`

**Community:** [Engine Ports & Adapters](Engine_Ports_%26_Adapters.md)

## Connections by Relation

### calls
- _job() `EXTRACTED`
- _job() `EXTRACTED`
- _seed_run() `EXTRACTED`
- _meta() `EXTRACTED`
- plan() `EXTRACTED`
- _jr() `EXTRACTED`
- _job() `EXTRACTED`
- _timeout_built() `EXTRACTED`
- _job_def() `EXTRACTED`
- test_offload_unblocks_oversized_docstring_real() `EXTRACTED`
- _sample_run() `EXTRACTED`
- test_offload_round_trip_real() `EXTRACTED`
- _job() `EXTRACTED`
- _jr() `EXTRACTED`
- _meta() `EXTRACTED`
- test_render_text_shows_step_level_report_refs() `EXTRACTED`
- test_meta_json_holds_pointers_not_payload() `EXTRACTED`
- test_reader_without_offloader_fails_loud_on_offloaded_meta() `EXTRACTED`
- test_reader_without_offloader_not_fooled_by_content_ref_as_text() `EXTRACTED`
- test_restore_uses_uri_not_current_prefix() `EXTRACTED`

### contains
- model.py `EXTRACTED`

### imports
- test_schedule.py `EXTRACTED`
- test_fargate_engine.py `EXTRACTED`
- test_stores.py `EXTRACTED`
- test_project.py `EXTRACTED`
- test_lifecycle_states.py `EXTRACTED`
- serialize.py `EXTRACTED`
- project.py `EXTRACTED`
- wire.py `EXTRACTED`
- test_cloud_reconcile.py `EXTRACTED`
- test_wire.py `EXTRACTED`
- test_conditional_writes.py `EXTRACTED`
- test_report_store.py `EXTRACTED`
- schedule.py `EXTRACTED`
- test_subprocess_engine.py `EXTRACTED`
- test_reconcile.py `EXTRACTED`
- test_cloud_integration.py `EXTRACTED`
- test_persist.py `EXTRACTED`
- ports.py `EXTRACTED`
- test_ddb_run_store.py `EXTRACTED`
- fargate_engine.py `EXTRACTED`

### rationale_for
- 一个 job = 一个 scope = 一个会话边界 = schedule 交给单个 worker 的活（ADR 0016/0024/0025）。 `EXTRACTED`

### uses
- CollectSink `INFERRED`
- FakeEngine `INFERRED`
- FakeResolver `INFERRED`
- ScheduleOpts `INFERRED`
- RunStore `INFERRED`
- EventRecord `INFERRED`
- TaskExited `INFERRED`
- _IncClock `INFERRED`
- FargateEngine `INFERRED`
- FeatureSource `INFERRED`
- ResultStore `INFERRED`
- Timing `INFERRED`
- Engine `INFERRED`
- ReportStore `INFERRED`
- Action `INFERRED`
- _Worker `INFERRED`
- _NetRaiseEngine `INFERRED`
- SubprocessEngine `INFERRED`
- _AbortProbeEngine `INFERRED`
- _FakeEcs `INFERRED`

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*