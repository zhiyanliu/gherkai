# RunState

> God node · 127 connections · `core/gherkai_core/model.py`

**Community:** [Run State Rendering](Run_State_Rendering.md)

## Connections by Relation

### calls
- _explain_run() `EXTRACTED`
- _seed_run() `EXTRACTED`
- _timeout_built() `EXTRACTED`
- _setup() `EXTRACTED`
- _setup() `EXTRACTED`
- test_explain_cloud_reads_evidence_from_s3() `EXTRACTED`
- _seed_finished_run() `EXTRACTED`
- _seed_for_build() `EXTRACTED`
- test_report_still_written_when_the_run_duration_read_fails() `EXTRACTED`
- test_run_state_timestamps_share_one_format() `EXTRACTED`
- test_offload_unblocks_oversized_docstring_real() `EXTRACTED`
- test_report_still_written_when_the_run_duration_read_fails() `EXTRACTED`
- test_offload_round_trip_real() `EXTRACTED`
- test_finalize_writes_verdicts_before_commit_point() `EXTRACTED`
- test_build_wires_arg_offloader_so_step_argument_bodies_read_back() `EXTRACTED`
- _cmd_submit() `EXTRACTED`
- test_tick_with_ddb_backend() `EXTRACTED`
- test_detached_flag_on_state_item() `EXTRACTED`
- test_worker_task_def_arns_on_state_item() `EXTRACTED`
- _mk_state() `EXTRACTED`

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
- test_arg_offload.py `EXTRACTED`
- run_store/ddb.py `EXTRACTED`
- persist.py `EXTRACTED`
- test_local_run_store_atomic.py `EXTRACTED`

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
- run_state_to_dict() `EXTRACTED`
- run_state_from_dict() `EXTRACTED`
- .project_state() `EXTRACTED`
- .save_run() `EXTRACTED`
- .create_run() `EXTRACTED`
- .load_run_state() `EXTRACTED`
- _state_scalars() `EXTRACTED`
- .project_state() `EXTRACTED`
- _big_state() `EXTRACTED`
- _state() `EXTRACTED`

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
- _FakeEcsClient `INFERRED`
- Sink `INFERRED`

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*