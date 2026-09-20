# Job

> God node · 134 connections · `core/gherkai_core/model.py`

**Community:** [Run Metadata & S3 Offload](Run_Metadata_%26_S3_Offload.md)

## Connections by Relation

### calls
- _job() `EXTRACTED`
- plan() `EXTRACTED`
- _meta() `EXTRACTED`
- _job() `EXTRACTED`
- _seed_run() `EXTRACTED`
- _jr() `EXTRACTED`
- _timeout_built() `EXTRACTED`
- _job() `EXTRACTED`
- _job_def() `EXTRACTED`
- _seed_finished_run() `EXTRACTED`
- test_offload_unblocks_oversized_docstring_real() `EXTRACTED`
- test_report_still_written_when_the_run_duration_read_fails() `EXTRACTED`
- test_explain_to_dict_drops_unmatched_scopes_and_keeps_job_fact() `EXTRACTED`
- _sample_run() `EXTRACTED`
- test_offload_round_trip_real() `EXTRACTED`
- _job() `EXTRACTED`
- _jr() `EXTRACTED`
- test_build_wires_arg_offloader_so_step_argument_bodies_read_back() `EXTRACTED`
- test_detached_flag_on_state_item() `EXTRACTED`
- test_worker_task_def_arns_on_state_item() `EXTRACTED`

### contains
- model.py `EXTRACTED`

### imports
- test_fargate_engine.py `EXTRACTED`
- test_schedule.py `EXTRACTED`
- test_project.py `EXTRACTED`
- test_stores.py `EXTRACTED`
- test_lifecycle_states.py `EXTRACTED`
- serialize.py `EXTRACTED`
- test_conditional_writes.py `EXTRACTED`
- project.py `EXTRACTED`
- test_cloud_reconcile.py `EXTRACTED`
- test_report_store.py `EXTRACTED`
- wire.py `EXTRACTED`
- test_reconcile.py `EXTRACTED`
- test_wire.py `EXTRACTED`
- test_subprocess_engine.py `EXTRACTED`
- ports.py `EXTRACTED`
- schedule.py `EXTRACTED`
- test_cloud_integration.py `EXTRACTED`
- test_persist.py `EXTRACTED`
- test_ddb_run_store.py `EXTRACTED`
- test_arg_offload.py `EXTRACTED`

### rationale_for
- 一个 job 就是一个 scope、一个会话边界，也就是 schedule 交给单个 worker 的活（ADR 0016/0024/0025）。 `EXTRACTED`

### uses
- CollectSink `INFERRED`
- FakeEngine `INFERRED`
- FakeResolver `INFERRED`
- ScheduleOpts `INFERRED`
- EventRecord `INFERRED`
- RunStore `INFERRED`
- FargateEngine `INFERRED`
- FeatureSource `INFERRED`
- TaskExited `INFERRED`
- ResultStore `INFERRED`
- _IncClock `INFERRED`
- _FakeEcs `INFERRED`
- Timing `INFERRED`
- Engine `INFERRED`
- ReportStore `INFERRED`
- SubprocessEngine `INFERRED`
- Action `INFERRED`
- NonTerminalSnapshot `INFERRED`
- _Worker `INFERRED`
- _NetRaiseEngine `INFERRED`

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*