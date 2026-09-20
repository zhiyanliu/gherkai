# JobState

> God node · 101 connections · `core/gherkai_core/model.py`

**Community:** [Run State Rendering](Run_State_Rendering.md)

## Connections by Relation

### calls
- project() `EXTRACTED`
- _explain_run() `EXTRACTED`
- _initial() `EXTRACTED`
- _seed_run() `EXTRACTED`
- _timeout_built() `EXTRACTED`
- _setup() `EXTRACTED`
- _setup() `EXTRACTED`
- test_explain_cloud_reads_evidence_from_s3() `EXTRACTED`
- _seed_finished_run() `EXTRACTED`
- _seed_for_build() `EXTRACTED`
- test_report_still_written_when_the_run_duration_read_fails() `EXTRACTED`
- test_run_state_timestamps_share_one_format() `EXTRACTED`
- test_report_still_written_when_the_run_duration_read_fails() `EXTRACTED`
- test_finalize_writes_verdicts_before_commit_point() `EXTRACTED`
- test_build_wires_arg_offloader_so_step_argument_bodies_read_back() `EXTRACTED`
- _cmd_submit() `EXTRACTED`
- run_state_from_result() `EXTRACTED`
- test_tick_with_ddb_backend() `EXTRACTED`
- test_detached_flag_on_state_item() `EXTRACTED`
- test_worker_task_def_arns_on_state_item() `EXTRACTED`

### contains
- model.py `EXTRACTED`

### imports
- test_project.py `EXTRACTED`
- test_stores.py `EXTRACTED`
- serialize.py `EXTRACTED`
- test_conditional_writes.py `EXTRACTED`
- project.py `EXTRACTED`
- test_cloud_reconcile.py `EXTRACTED`
- test_reconcile.py `EXTRACTED`
- ports.py `EXTRACTED`
- test_cloud_integration.py `EXTRACTED`
- run_store/local.py `EXTRACTED`
- test_ddb_run_store.py `EXTRACTED`
- run_store/ddb.py `EXTRACTED`
- persist.py `EXTRACTED`
- test_local_run_store_atomic.py `EXTRACTED`

### rationale_for
- 单个 job 的控制面运行态（执行后才有）。 `EXTRACTED`

### references
- projected_run_status() `EXTRACTED`
- .update_job_state() `EXTRACTED`
- _job_state_to_item() `EXTRACTED`
- .update_job_state() `EXTRACTED`
- _job_state_from_item() `EXTRACTED`
- .update_job_state() `EXTRACTED`

### uses
- LocalRunStore `INFERRED`
- DynamoDBRunStore `INFERRED`
- EventRecord `INFERRED`
- RunStore `INFERRED`
- RunPersistence `INFERRED`
- TaskExited `INFERRED`
- ResultStore `INFERRED`
- _FakeEcs `INFERRED`
- Timing `INFERRED`
- Engine `INFERRED`
- ReportStore `INFERRED`
- Action `INFERRED`
- NonTerminalSnapshot `INFERRED`
- FakeLauncher `INFERRED`
- _FakeSchedulerClient `INFERRED`
- EngineResolver `INFERRED`
- JobSink `INFERRED`
- _RecorderWatch `INFERRED`
- Sink `INFERRED`
- _FakeStartEngine `INFERRED`

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*