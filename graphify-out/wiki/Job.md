# Job

> God node · 129 connections · `core/gherkai_core/model.py`

**Community:** [Run Definition Domain Model](Run_Definition_Domain_Model.md)

## Connections by Relation

### calls
- _job() `EXTRACTED`
- _meta() `EXTRACTED`
- plan() `EXTRACTED`
- _job() `EXTRACTED`
- _seed_run() `EXTRACTED`
- _jr() `EXTRACTED`
- _timeout_built() `EXTRACTED`
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
- test_run_tree_attaches_reason_and_refs_under_their_step() `EXTRACTED`
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
- project.py `EXTRACTED`
- test_conditional_writes.py `EXTRACTED`
- wire.py `EXTRACTED`
- test_cloud_reconcile.py `EXTRACTED`
- test_report_store.py `EXTRACTED`
- test_wire.py `EXTRACTED`
- test_reconcile.py `EXTRACTED`
- schedule.py `EXTRACTED`
- ports.py `EXTRACTED`
- test_cloud_integration.py `EXTRACTED`
- test_persist.py `EXTRACTED`
- test_ddb_run_store.py `EXTRACTED`
- fargate_engine.py `EXTRACTED`
- reconcile.py `EXTRACTED`

### rationale_for
- 一个 job 就是一个 scope、一个会话边界，也就是 schedule 交给单个 worker 的活（ADR 0016/0024/0025）。 `EXTRACTED`

### uses
- CollectSink `INFERRED`
- FakeEngine `INFERRED`
- FakeResolver `INFERRED`
- ScheduleOpts `INFERRED`
- EventRecord `INFERRED`
- TaskExited `INFERRED`
- _IncClock `INFERRED`
- RunStore `INFERRED`
- _FakeEcs `INFERRED`
- FargateEngine `INFERRED`
- Timing `INFERRED`
- FeatureSource `INFERRED`
- ResultStore `INFERRED`
- Action `INFERRED`
- NonTerminalSnapshot `INFERRED`
- _Worker `INFERRED`
- _NetRaiseEngine `INFERRED`
- _AbortProbeEngine `INFERRED`
- FakeLauncher `INFERRED`
- CloudLauncher `INFERRED`

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*