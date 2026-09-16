# Status

> God node · 105 connections · `core/gherkai_core/model.py`

**Community:** [Cloud Boto3 Guards & EventLog](Cloud_Boto3_Guards_%26_EventLog.md)

## Connections by Relation

### calls
- event_from_json() `EXTRACTED`
- job_result_from_dict() `EXTRACTED`
- from_dict() `EXTRACTED`
- run_state_from_dict() `EXTRACTED`
- .load_run_state() `EXTRACTED`
- _job_state_from_item() `EXTRACTED`

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
- test_cloud_reconcile.py `EXTRACTED`
- test_report_store.py `EXTRACTED`
- wire.py `EXTRACTED`
- test_conditional_writes.py `EXTRACTED`
- test_reconcile.py `EXTRACTED`
- test_wire.py `EXTRACTED`
- test_subprocess_engine.py `EXTRACTED`
- schedule.py `EXTRACTED`
- test_cloud_integration.py `EXTRACTED`
- test_persist.py `EXTRACTED`
- run_store/local.py `EXTRACTED`
- test_ddb_run_store.py `EXTRACTED`
- test_arg_offload.py `EXTRACTED`

### inherits
- Enum `EXTRACTED`
- str `EXTRACTED`

### rationale_for
- 判定态（ADR 0024 三态）+ core 派生态/前置态（ADR 0031）。 worker 经 wire… `EXTRACTED`

### references
- _aggregate() `EXTRACTED`
- reduce_event() `EXTRACTED`
- _reduce_scope() `EXTRACTED`
- _jr() `EXTRACTED`
- projected_run_status() `EXTRACTED`
- severity() `EXTRACTED`
- _lifecycle_rank() `EXTRACTED`
- ._reduce() `EXTRACTED`
- .finalize_run() `EXTRACTED`
- _job_status() `EXTRACTED`
- .try_finalize() `EXTRACTED`
- _state() `EXTRACTED`
- .finalize_run() `EXTRACTED`
- .try_finalize() `EXTRACTED`
- .try_finalize() `EXTRACTED`
- .finalize_run() `EXTRACTED`

### uses
- LocalRunStore `INFERRED`
- ScheduleOpts `INFERRED`
- DynamoDBRunStore `INFERRED`
- EventRecord `INFERRED`
- RunStore `INFERRED`
- TaskExited `INFERRED`
- RunPersistence `INFERRED`
- ResultStore `INFERRED`
- _IncClock `INFERRED`
- Timing `INFERRED`
- _FakeEcs `INFERRED`
- Engine `INFERRED`
- ReportStore `INFERRED`
- Aws `INFERRED`
- Action `INFERRED`
- NonTerminalSnapshot `INFERRED`
- _Worker `INFERRED`
- _NetRaiseEngine `INFERRED`
- _AbortProbeEngine `INFERRED`
- FakeLauncher `INFERRED`

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*