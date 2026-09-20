# RunMeta

> God node · 119 connections · `core/gherkai_core/model.py`

**Community:** [Run Metadata & S3 Offload](Run_Metadata_%26_S3_Offload.md)

## Connections by Relation

### calls
- _sample_run() `EXTRACTED`
- _explain_run() `EXTRACTED`
- _seed_run() `EXTRACTED`
- _rr() `EXTRACTED`
- _timeout_built() `EXTRACTED`
- _setup() `EXTRACTED`
- _seed_finished_run() `EXTRACTED`
- _seed_for_build() `EXTRACTED`
- test_report_still_written_when_the_run_duration_read_fails() `EXTRACTED`
- test_run_state_timestamps_share_one_format() `EXTRACTED`
- test_offload_unblocks_oversized_docstring_real() `EXTRACTED`
- test_report_still_written_when_the_run_duration_read_fails() `EXTRACTED`
- _sample_run() `EXTRACTED`
- test_offload_round_trip_real() `EXTRACTED`
- test_build_wires_arg_offloader_so_step_argument_bodies_read_back() `EXTRACTED`
- test_detached_flag_on_state_item() `EXTRACTED`
- test_worker_task_def_arns_on_state_item() `EXTRACTED`
- test_index_html_shortcircuit_note_matches_cli_wording() `EXTRACTED`
- test_render_text_shows_step_level_report_refs() `EXTRACTED`
- test_render_text_step_reason_line_is_single_line_and_only_when_present() `EXTRACTED`

### contains
- model.py `EXTRACTED`

### imports
- test_schedule.py `EXTRACTED`
- test_project.py `EXTRACTED`
- test_stores.py `EXTRACTED`
- serialize.py `EXTRACTED`
- test_conditional_writes.py `EXTRACTED`
- project.py `EXTRACTED`
- test_cloud_reconcile.py `EXTRACTED`
- test_report_store.py `EXTRACTED`
- test_reconcile.py `EXTRACTED`
- test_subprocess_engine.py `EXTRACTED`
- ports.py `EXTRACTED`
- schedule.py `EXTRACTED`
- test_cloud_integration.py `EXTRACTED`
- test_persist.py `EXTRACTED`
- run_store/local.py `EXTRACTED`
- test_ddb_run_store.py `EXTRACTED`
- test_arg_offload.py `EXTRACTED`
- test_sqlite_event_log.py `EXTRACTED`
- run_store/ddb.py `EXTRACTED`
- reconcile.py `EXTRACTED`

### rationale_for
- 一次 run 的 **definition**（前置身份，执行前由 plan 产出 + 组合根生成确定，不从 RunResult 反推）。… `EXTRACTED`

### references
- schedule() `EXTRACTED`
- _rm() `EXTRACTED`
- project() `EXTRACTED`
- _meta() `EXTRACTED`
- tick() `EXTRACTED`
- _meta() `EXTRACTED`
- _initial() `EXTRACTED`
- project_full() `EXTRACTED`
- run_reconcile_loop() `EXTRACTED`
- run_meta_to_dict() `EXTRACTED`
- run_meta_from_dict() `EXTRACTED`
- _meta() `EXTRACTED`
- .create_run() `EXTRACTED`
- .save_run() `EXTRACTED`
- _rm() `EXTRACTED`
- _meta() `EXTRACTED`
- .save_run() `EXTRACTED`
- .create_run() `EXTRACTED`
- .begin() `EXTRACTED`
- _build_run_meta() `EXTRACTED`

### uses
- LocalRunStore `INFERRED`
- ScheduleOpts `INFERRED`
- DynamoDBRunStore `INFERRED`
- EventRecord `INFERRED`
- RunStore `INFERRED`
- RunPersistence `INFERRED`
- TaskExited `INFERRED`
- ResultStore `INFERRED`
- _IncClock `INFERRED`
- _FakeEcs `INFERRED`
- Timing `INFERRED`
- Engine `INFERRED`
- ReportStore `INFERRED`
- Action `INFERRED`
- NonTerminalSnapshot `INFERRED`
- _Worker `INFERRED`
- FakeLauncher `INFERRED`
- _FakeSchedulerClient `INFERRED`
- SubprocessLauncher `INFERRED`
- EngineResolver `INFERRED`

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*