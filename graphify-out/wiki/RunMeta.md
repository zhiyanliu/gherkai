# RunMeta

> God node · 107 connections · `core/gherkai_core/model.py`

**Community:** [Run State Rendering & Boto Guard](Run_State_Rendering_%26_Boto_Guard.md)

## Connections by Relation

### calls
- _sample_run() `EXTRACTED`
- _seed_run() `EXTRACTED`
- _rr() `EXTRACTED`
- _cmd_run() `EXTRACTED`
- _cmd_submit() `EXTRACTED`
- _timeout_built() `EXTRACTED`
- _setup() `EXTRACTED`
- test_run_state_timestamps_share_one_format() `EXTRACTED`
- test_offload_unblocks_oversized_docstring_real() `EXTRACTED`
- _sample_run() `EXTRACTED`
- test_offload_round_trip_real() `EXTRACTED`
- _seed_for_build() `EXTRACTED`
- test_render_text_shows_step_level_report_refs() `EXTRACTED`
- test_meta_json_holds_pointers_not_payload() `EXTRACTED`
- test_reader_without_offloader_fails_loud_on_offloaded_meta() `EXTRACTED`
- test_reader_without_offloader_not_fooled_by_content_ref_as_text() `EXTRACTED`
- test_restore_uses_uri_not_current_prefix() `EXTRACTED`
- test_detached_flag_on_state_item() `EXTRACTED`
- test_worker_task_def_arns_on_state_item() `EXTRACTED`
- test_render_text_annotates_shortcircuited_step() `EXTRACTED`

### contains
- model.py `EXTRACTED`

### imports
- test_schedule.py `EXTRACTED`
- test_stores.py `EXTRACTED`
- test_project.py `EXTRACTED`
- serialize.py `EXTRACTED`
- project.py `EXTRACTED`
- test_cloud_reconcile.py `EXTRACTED`
- test_conditional_writes.py `EXTRACTED`
- test_report_store.py `EXTRACTED`
- schedule.py `EXTRACTED`
- test_subprocess_engine.py `EXTRACTED`
- test_reconcile.py `EXTRACTED`
- test_cloud_integration.py `EXTRACTED`
- test_persist.py `EXTRACTED`
- ports.py `EXTRACTED`
- test_ddb_run_store.py `EXTRACTED`
- test_arg_offload.py `EXTRACTED`
- reconcile.py `EXTRACTED`
- run_store/ddb.py `EXTRACTED`
- run_store/local.py `EXTRACTED`
- test_sqlite_event_log.py `EXTRACTED`

### rationale_for
- 一次 run 的 **definition**（前置身份，执行前由 plan 产出 + 组合根生成确定，不从 RunResult 反推）。… `EXTRACTED`

### references
- [schedule()](schedule%28%29.md) `EXTRACTED`
- _rm() `EXTRACTED`
- project() `EXTRACTED`
- _meta() `EXTRACTED`
- tick() `EXTRACTED`
- _meta() `EXTRACTED`
- _initial() `EXTRACTED`
- run_meta_to_dict() `EXTRACTED`
- run_reconcile_loop() `EXTRACTED`
- run_meta_from_dict() `EXTRACTED`
- project_full() `EXTRACTED`
- _meta() `EXTRACTED`
- .create_run() `EXTRACTED`
- _rm() `EXTRACTED`
- .save_run() `EXTRACTED`
- _meta() `EXTRACTED`
- .save_run() `EXTRACTED`
- .create_run() `EXTRACTED`
- .begin() `EXTRACTED`
- .load_run_meta() `EXTRACTED`

### uses
- LocalRunStore `INFERRED`
- ScheduleOpts `INFERRED`
- DynamoDBRunStore `INFERRED`
- RunStore `INFERRED`
- EventRecord `INFERRED`
- RunPersistence `INFERRED`
- TaskExited `INFERRED`
- _IncClock `INFERRED`
- ResultStore `INFERRED`
- Timing `INFERRED`
- Engine `INFERRED`
- ReportStore `INFERRED`
- Action `INFERRED`
- _Worker `INFERRED`
- _FakeEcs `INFERRED`
- EngineResolver `INFERRED`
- Sink `INFERRED`
- FakeLauncher `INFERRED`
- JobSink `INFERRED`
- _RecorderWatch `INFERRED`

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*