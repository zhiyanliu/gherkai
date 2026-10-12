# Fargate Engine Adapter Tests

> 33 nodes · cohesion 0.09

## Key Concepts

- **test_fargate_engine.py** (76 connections) — `core/tests/test_fargate_engine.py`
- **_spy_run_task_env()** (9 connections) — `core/tests/test_fargate_engine.py`
- **_engine_with_fake_ecs()** (8 connections) — `core/tests/test_fargate_engine.py`
- **_await_engine()** (6 connections) — `core/tests/test_fargate_engine.py`
- **_stopped_resp()** (4 connections) — `core/tests/test_fargate_engine.py`
- **test_artifact_injection_kwargs_are_mandatory()** (3 connections) — `core/tests/test_fargate_engine.py`
- **test_await_exit_code_missing_task_beyond_grace_raises()** (3 connections) — `core/tests/test_fargate_engine.py`
- **test_await_exit_code_null_beyond_grace_settles_as_error()** (3 connections) — `core/tests/test_fargate_engine.py`
- **test_await_exit_code_null_then_nonzero_landed_preserved()** (3 connections) — `core/tests/test_fargate_engine.py`
- **test_await_exit_code_waits_out_null_then_reads_landed_code()** (3 connections) — `core/tests/test_fargate_engine.py`
- **test_probe_task_missing_is_a_third_state_not_running()** (3 connections) — `core/tests/test_fargate_engine.py`
- **test_raise_for_worker_exit_maps_codes_with_fargate_label()** (3 connections) — `core/tests/test_fargate_engine.py`
- **test_run_scope_injects_artifact_s3_env()** (3 connections) — `core/tests/test_fargate_engine.py`
- **test_run_scope_injects_region_never_profile()** (3 connections) — `core/tests/test_fargate_engine.py`
- **test_run_scope_injects_sdk_artifact_dir_env()** (3 connections) — `core/tests/test_fargate_engine.py`
- **test_run_scope_omits_artifact_s3_when_none()** (3 connections) — `core/tests/test_fargate_engine.py`
- **test_run_scope_omits_region_when_none()** (3 connections) — `core/tests/test_fargate_engine.py`
- **test_runtask_injects_extra_env()** (3 connections) — `core/tests/test_fargate_engine.py`
- **test_await_exit_code_transient_missing_then_stopped_reads_code()** (2 connections) — `core/tests/test_fargate_engine.py`
- **test_final_drain_logs_real_holes_under_consistent_read()** (2 connections) — `core/tests/test_fargate_engine.py`
- **test_final_drain_paginates_across_last_evaluated_key()** (2 connections) — `core/tests/test_fargate_engine.py`
- **test_probe_task_not_stopped()** (2 connections) — `core/tests/test_fargate_engine.py`
- **test_probe_task_stopped_but_exit_code_null()** (2 connections) — `core/tests/test_fargate_engine.py`
- **test_probe_task_stopped_with_exit_code()** (2 connections) — `core/tests/test_fargate_engine.py`
- **FargateEngine adapter 单测（ADR 0024「DynamoDB 作 events-out」）。…** (1 connections) — `core/tests/test_fargate_engine.py`
- *... and 8 more nodes in this community*

## Relationships

- [Fargate Event Drain Tests](Fargate_Event_Drain_Tests.md) (28 shared connections)
- [Job/Scenario Explain Model](Job-Scenario_Explain_Model.md) (12 shared connections)
- [Event Read Gap Handling](Event_Read_Gap_Handling.md) (9 shared connections)
- [Cloud Launcher & Fargate Adapters](Cloud_Launcher_%26_Fargate_Adapters.md) (8 shared connections)
- [DynamoDB Event Log](DynamoDB_Event_Log.md) (4 shared connections)
- [Event Progress Formatting](Event_Progress_Formatting.md) (2 shared connections)
- [Fake DDB Table & SQLite Records](Fake_DDB_Table_%26_SQLite_Records.md) (1 shared connections)
- [Feature Parsing & Errors](Feature_Parsing_%26_Errors.md) (1 shared connections)

## Source Files

- `core/tests/test_fargate_engine.py`

## Audit Trail

- EXTRACTED: 114 (100%)
- INFERRED: 0 (0%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*