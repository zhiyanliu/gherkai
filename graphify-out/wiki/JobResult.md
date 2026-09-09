# JobResult

> God node · 72 connections · `core/gherkai_core/model.py`

**Community:** [Run Result Verdict Model](Run_Result_Verdict_Model.md)

## Connections by Relation

### calls
- _sample_run() `EXTRACTED`
- _sample_run() `EXTRACTED`
- test_render_text_shows_step_level_report_refs() `EXTRACTED`
- test_render_text_annotates_shortcircuited_step() `EXTRACTED`
- test_render_text_no_annotation_on_plain_failed() `EXTRACTED`
- test_new_states_round_trip() `EXTRACTED`
- test_result_store_scope_id_not_path_traversal() `EXTRACTED`
- test_prefix_isolates_runs() `EXTRACTED`
- test_load_all_paginated_preserves_failed_verdict() `EXTRACTED`
- test_load_all_paginates_beyond_1000() `EXTRACTED`
- test_load_all_stable_order() `EXTRACTED`
- test_scope_id_with_slash_not_subprefix() `EXTRACTED`

### contains
- model.py `EXTRACTED`

### imports
- test_stores.py `EXTRACTED`
- test_lifecycle_states.py `EXTRACTED`
- serialize.py `EXTRACTED`
- project.py `EXTRACTED`
- test_report_store.py `EXTRACTED`
- schedule.py `EXTRACTED`
- test_persist.py `EXTRACTED`
- ports.py `EXTRACTED`
- persist.py `EXTRACTED`
- test_s3_result_store.py `EXTRACTED`
- result_store/local.py `EXTRACTED`
- result_store/s3.py `EXTRACTED`

### method
- .engine() `EXTRACTED`
- .scope_id() `EXTRACTED`
- .scope_name() `EXTRACTED`

### rationale_for
- 单个 job(=scope) 的归约结果（数据面判定 + 持有它的 definition）。 **持有… `EXTRACTED`

### references
- job_result_from_dict() `EXTRACTED`
- _rr() `EXTRACTED`
- _jr() `EXTRACTED`
- job_result_to_dict() `EXTRACTED`
- _reduce_scope() `EXTRACTED`
- reduce_event() `EXTRACTED`
- _jr() `EXTRACTED`
- ._run_once() `EXTRACTED`
- ._reduce() `EXTRACTED`
- .load_all() `EXTRACTED`
- .save_job_result() `EXTRACTED`
- .on_job_complete() `EXTRACTED`
- .load_job_result() `EXTRACTED`
- .load_all() `EXTRACTED`
- .save_job_result() `EXTRACTED`
- .load_job_result() `EXTRACTED`
- .run() `EXTRACTED`
- .load_all() `EXTRACTED`
- .__call__() `EXTRACTED`
- .save_job_result() `EXTRACTED`

### uses
- ScheduleOpts `INFERRED`
- RunStore `INFERRED`
- EventRecord `INFERRED`
- RunPersistence `INFERRED`
- TaskExited `INFERRED`
- ResultStore `INFERRED`
- Timing `INFERRED`
- Engine `INFERRED`
- ReportStore `INFERRED`
- Action `INFERRED`
- _Worker `INFERRED`
- _NetRaiseEngine `INFERRED`
- LocalResultStore `INFERRED`
- S3ResultStore `INFERRED`
- _AbortProbeEngine `INFERRED`
- EngineResolver `INFERRED`
- Sink `INFERRED`
- JobSink `INFERRED`
- _Heartbeat `INFERRED`
- _FakeTable `INFERRED`

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*