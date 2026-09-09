# RunState

> God node · 104 connections · `core/gherkai_core/model.py`

**Community:** [Run State Rendering](Run_State_Rendering.md)

## Connections by Relation

### calls
- _seed_run() `EXTRACTED`
- _cmd_submit() `EXTRACTED`
- _timeout_built() `EXTRACTED`
- _setup() `EXTRACTED`
- _setup() `EXTRACTED`
- test_run_state_timestamps_share_one_format() `EXTRACTED`
- test_offload_unblocks_oversized_docstring_real() `EXTRACTED`
- test_offload_round_trip_real() `EXTRACTED`
- test_tick_with_ddb_backend() `EXTRACTED`
- _seed_for_build() `EXTRACTED`
- test_meta_json_holds_pointers_not_payload() `EXTRACTED`
- test_reader_without_offloader_fails_loud_on_offloaded_meta() `EXTRACTED`
- test_reader_without_offloader_not_fooled_by_content_ref_as_text() `EXTRACTED`
- test_detached_flag_on_state_item() `EXTRACTED`
- test_worker_task_def_arns_on_state_item() `EXTRACTED`
- _mk_state() `EXTRACTED`
- test_ddb_state_item_grows_past_400kb_on_incremental_update_real() `EXTRACTED`
- test_build_local_reconcile_reads_steps_dir_from_definition() `EXTRACTED`
- test_build_local_reconcile_resolves_region_like_foreground() `EXTRACTED`
- test_docstring_starting_with_s3_scheme_survives() `EXTRACTED`

### contains
- model.py `EXTRACTED`

### imports
- test_stores.py `EXTRACTED`
- test_project.py `EXTRACTED`
- serialize.py `EXTRACTED`
- project.py `EXTRACTED`
- test_cloud_reconcile.py `EXTRACTED`
- test_conditional_writes.py `EXTRACTED`
- test_reconcile.py `EXTRACTED`
- test_cloud_integration.py `EXTRACTED`
- ports.py `EXTRACTED`
- test_ddb_run_store.py `EXTRACTED`
- test_arg_offload.py `EXTRACTED`
- run_store/ddb.py `EXTRACTED`
- run_store/local.py `EXTRACTED`
- persist.py `EXTRACTED`

### rationale_for
- 一次 run 的**控制面运行态**（status/血缘/起止；执行后产生，ADR 0016 控制面）。 与… `EXTRACTED`

### references
- project() `EXTRACTED`
- _initial() `EXTRACTED`
- plan_next() `EXTRACTED`
- run_state_from_result() `EXTRACTED`
- _initial_state() `EXTRACTED`
- .create_run() `EXTRACTED`
- .save_run() `EXTRACTED`
- ._write_state() `EXTRACTED`
- .load_run_state() `EXTRACTED`
- render_run_state() `EXTRACTED`
- .project_state() `EXTRACTED`
- run_state_from_dict() `EXTRACTED`
- .save_run() `EXTRACTED`
- .create_run() `EXTRACTED`
- run_state_to_dict() `EXTRACTED`
- .load_run_state() `EXTRACTED`
- _state_scalars() `EXTRACTED`
- .project_state() `EXTRACTED`
- _state() `EXTRACTED`
- .create_run() `EXTRACTED`

### uses
- LocalRunStore `INFERRED`
- DynamoDBRunStore `INFERRED`
- RunStore `INFERRED`
- EventRecord `INFERRED`
- RunPersistence `INFERRED`
- TaskExited `INFERRED`
- ResultStore `INFERRED`
- Timing `INFERRED`
- Engine `INFERRED`
- ReportStore `INFERRED`
- Action `INFERRED`
- _FakeEcs `INFERRED`
- EngineResolver `INFERRED`
- Sink `INFERRED`
- FakeLauncher `INFERRED`
- JobSink `INFERRED`
- _RecorderWatch `INFERRED`
- _FakeSchedulerClient `INFERRED`
- _FakeStartEngine `INFERRED`
- WorkerHandle `INFERRED`

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*