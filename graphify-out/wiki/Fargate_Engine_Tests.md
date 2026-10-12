# Fargate Engine Tests

> 31 nodes · cohesion 0.10

## Key Concepts

- **test_fargate_engine.py** (76 connections) — `core/tests/test_fargate_engine.py`
- **_spy_run_task_env()** (9 connections) — `core/tests/test_fargate_engine.py`
- **_engine_with_fake_ecs()** (8 connections) — `core/tests/test_fargate_engine.py`
- **_await_engine()** (6 connections) — `core/tests/test_fargate_engine.py`
- **_stopped_resp()** (4 connections) — `core/tests/test_fargate_engine.py`
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
- **_final_drain 终读须翻页：>1MB 尾部 DDB Query 分页返回 LastEvaluatedKey，不循环…** (1 connections) — `core/tests/test_fargate_engine.py`
- *... and 6 more nodes in this community*

## Relationships

- [Worker Exit Drain Tests](Worker_Exit_Drain_Tests.md) (29 shared connections)
- [ECS Event Gap Handling](ECS_Event_Gap_Handling.md) (8 shared connections)
- [Fargate Engine Adapter](Fargate_Engine_Adapter.md) (5 shared connections)
- [Fargate Worker Handle](Fargate_Worker_Handle.md) (5 shared connections)
- [Cloud Adapter Boundary Modules](Cloud_Adapter_Boundary_Modules.md) (5 shared connections)
- [Job Explain Data Model](Job_Explain_Data_Model.md) (3 shared connections)
- [Event Exit Records & Keys](Event_Exit_Records_%26_Keys.md) (2 shared connections)
- [Event Wire Protocol](Event_Wire_Protocol.md) (2 shared connections)
- [Eventual Consistency Read Tests](Eventual_Consistency_Read_Tests.md) (2 shared connections)
- [Terminal State Aggregation](Terminal_State_Aggregation.md) (1 shared connections)
- [Reconciler Event Projection](Reconciler_Event_Projection.md) (1 shared connections)
- [Run Scheduling Events Core](Run_Scheduling_Events_Core.md) (1 shared connections)

## Source Files

- `core/tests/test_fargate_engine.py`

## Audit Trail

- EXTRACTED: 112 (100%)
- INFERRED: 0 (0%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*