# JobResult

> God node · 83 connections · `core/gherkai_core/model.py`

**Community:** [S3 Result Store](S3_Result_Store.md)

## Connections by Relation

### calls
- _sample_run() `EXTRACTED`
- _explain_run() `EXTRACTED`
- test_explain_cloud_reads_evidence_from_s3() `EXTRACTED`
- test_explain_to_dict_drops_unmatched_scopes_and_keeps_job_fact() `EXTRACTED`
- _sample_run() `EXTRACTED`
- test_index_html_shortcircuit_note_matches_cli_wording() `EXTRACTED`
- test_render_text_shows_step_level_report_refs() `EXTRACTED`
- test_render_text_step_reason_line_is_single_line_and_only_when_present() `EXTRACTED`
- test_render_text_annotates_shortcircuited_step() `EXTRACTED`
- test_render_text_no_annotation_on_plain_failed() `EXTRACTED`
- test_job_line_with_error_type_but_no_message_has_no_orphan_colon() `EXTRACTED`
- test_render_text_shows_reason_for_fail_fast_states() `EXTRACTED`
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
- test_local_result_store_atomic.py `EXTRACTED`
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
- _big_job_result() `EXTRACTED`
- explain_to_dict() `EXTRACTED`
- ._reduce() `EXTRACTED`
- .load_all() `EXTRACTED`
- .save_job_result() `EXTRACTED`
- .save_job_result() `EXTRACTED`
- .on_job_complete() `EXTRACTED`
- .load_job_result() `EXTRACTED`
- .load_all() `EXTRACTED`
- .load_job_result() `EXTRACTED`
- .run() `EXTRACTED`
- .load_all() `EXTRACTED`

### uses
- ScheduleOpts `INFERRED`
- EventRecord `INFERRED`
- RunStore `INFERRED`
- TaskExited `INFERRED`
- RunPersistence `INFERRED`
- ResultStore `INFERRED`
- Timing `INFERRED`
- LocalResultStore `INFERRED`
- Engine `INFERRED`
- ReportStore `INFERRED`
- Action `INFERRED`
- NonTerminalSnapshot `INFERRED`
- _Worker `INFERRED`
- _NetRaiseEngine `INFERRED`
- _AbortProbeEngine `INFERRED`
- S3ResultStore `INFERRED`
- EngineResolver `INFERRED`
- JobSink `INFERRED`
- Sink `INFERRED`
- _Heartbeat `INFERRED`

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*