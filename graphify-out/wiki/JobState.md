# JobState

> God node · 85 connections · `core/gherkai_core/model.py`

**Community:** [DynamoDB RunStore Conditional Writes](DynamoDB_RunStore_Conditional_Writes.md)

## Connections by Relation

### calls
- project() `EXTRACTED`
- _seed_run() `EXTRACTED`
- _initial() `EXTRACTED`
- _cmd_submit() `EXTRACTED`
- _timeout_built() `EXTRACTED`
- _setup() `EXTRACTED`
- _setup() `EXTRACTED`
- test_run_state_timestamps_share_one_format() `EXTRACTED`
- run_state_from_result() `EXTRACTED`
- test_tick_with_ddb_backend() `EXTRACTED`
- _seed_for_build() `EXTRACTED`
- test_detached_flag_on_state_item() `EXTRACTED`
- test_worker_task_def_arns_on_state_item() `EXTRACTED`
- _initial_state() `EXTRACTED`
- _mk_state() `EXTRACTED`
- test_ddb_state_item_grows_past_400kb_on_incremental_update_real() `EXTRACTED`
- test_build_local_reconcile_reads_steps_dir_from_definition() `EXTRACTED`
- test_build_local_reconcile_resolves_region_like_foreground() `EXTRACTED`
- test_ddb_empty_string_scalar_and_map_entry_real() `EXTRACTED`
- test_ddb_run_store_lifecycle_real() `EXTRACTED`

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
- run_store/ddb.py `EXTRACTED`
- run_store/local.py `EXTRACTED`
- persist.py `EXTRACTED`

### rationale_for
- 单个 job 的控制面运行态（执行后才有）。 `EXTRACTED`

### references
- projected_run_status() `EXTRACTED`
- _job_state_to_item() `EXTRACTED`
- .update_job_state() `EXTRACTED`
- .update_job_state() `EXTRACTED`
- _job_state_from_item() `EXTRACTED`
- .update_job_state() `EXTRACTED`

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