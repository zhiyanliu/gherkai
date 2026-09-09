# Status

> God node · 93 connections · `core/gherkai_core/model.py`

**Community:** [Boto Guard & S3 Offload](Boto_Guard_%26_S3_Offload.md)

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
- test_schedule.py `EXTRACTED`
- test_fargate_engine.py `EXTRACTED`
- test_stores.py `EXTRACTED`
- test_project.py `EXTRACTED`
- test_lifecycle_states.py `EXTRACTED`
- serialize.py `EXTRACTED`
- project.py `EXTRACTED`
- wire.py `EXTRACTED`
- test_cloud_reconcile.py `EXTRACTED`
- test_wire.py `EXTRACTED`
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
- _NetRaiseEngine `INFERRED`
- Aws `INFERRED`
- _AbortProbeEngine `INFERRED`
- _FakeEcs `INFERRED`
- EngineResolver `INFERRED`
- Sink `INFERRED`

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*