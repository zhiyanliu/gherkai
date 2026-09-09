# Fargate Engine Unit Tests

> 21 nodes · cohesion 0.16

## Key Concepts

- **test_fargate_engine.py** (62 connections) — `core/tests/test_fargate_engine.py`
- **_spy_run_task_env()** (9 connections) — `core/tests/test_fargate_engine.py`
- **_await_engine()** (6 connections) — `core/tests/test_fargate_engine.py`
- **_engine_with_fake_ecs()** (6 connections) — `core/tests/test_fargate_engine.py`
- **_stopped_resp()** (4 connections) — `core/tests/test_fargate_engine.py`
- **test_await_exit_code_null_beyond_grace_settles_as_error()** (3 connections) — `core/tests/test_fargate_engine.py`
- **test_await_exit_code_null_then_nonzero_landed_preserved()** (3 connections) — `core/tests/test_fargate_engine.py`
- **test_await_exit_code_waits_out_null_then_reads_landed_code()** (3 connections) — `core/tests/test_fargate_engine.py`
- **test_run_scope_injects_artifact_s3_env()** (3 connections) — `core/tests/test_fargate_engine.py`
- **test_run_scope_injects_region_never_profile()** (3 connections) — `core/tests/test_fargate_engine.py`
- **test_run_scope_injects_sdk_artifact_dir_env()** (3 connections) — `core/tests/test_fargate_engine.py`
- **test_run_scope_omits_artifact_s3_when_none()** (3 connections) — `core/tests/test_fargate_engine.py`
- **test_run_scope_omits_region_when_none()** (3 connections) — `core/tests/test_fargate_engine.py`
- **test_events_pk_composite_run_id_scope_id()** (2 connections) — `core/tests/test_fargate_engine.py`
- **test_final_drain_paginates_across_last_evaluated_key()** (2 connections) — `core/tests/test_fargate_engine.py`
- **test_probe_task_not_stopped()** (2 connections) — `core/tests/test_fargate_engine.py`
- **test_probe_task_stopped_but_exit_code_null()** (2 connections) — `core/tests/test_fargate_engine.py`
- **test_probe_task_stopped_with_exit_code()** (2 connections) — `core/tests/test_fargate_engine.py`
- **FargateEngine adapter 单测（ADR 0024「DynamoDB 作 events-out」）。…** (1 connections) — `core/tests/test_fargate_engine.py`
- **_final_drain 终读须翻页：>1MB 尾部 DDB Query 分页返回 LastEvaluatedKey，不循环…** (1 connections) — `core/tests/test_fargate_engine.py`
- **跑 run_scope、拦 run_task 抓 overrides env → 返回 {name: value} dict。** (1 connections) — `core/tests/test_fargate_engine.py`

## Relationships

- [Fargate Event Drain & Exit Codes](Fargate_Event_Drain_%26_Exit_Codes.md) (27 shared connections)
- [Engine Ports & Adapters](Engine_Ports_%26_Adapters.md) (10 shared connections)
- [Fargate Engine Adapter](Fargate_Engine_Adapter.md) (5 shared connections)
- [Cloud Launcher & DDB EventLog](Cloud_Launcher_%26_DDB_EventLog.md) (3 shared connections)
- [Event Formatting & Cost Model](Event_Formatting_%26_Cost_Model.md) (2 shared connections)
- [Worker Exit Code Translation](Worker_Exit_Code_Translation.md) (2 shared connections)
- [Scope Done vs ECS Stopped](Scope_Done_vs_ECS_Stopped.md) (2 shared connections)
- [Fargate Worker Handle](Fargate_Worker_Handle.md) (1 shared connections)
- [Terminal Status Aggregation](Terminal_Status_Aggregation.md) (1 shared connections)
- [SQLite Event Log & Projection](SQLite_Event_Log_%26_Projection.md) (1 shared connections)
- [Run Result Verdict Model](Run_Result_Verdict_Model.md) (1 shared connections)
- [Exit Item Test Setup](Exit_Item_Test_Setup.md) (1 shared connections)

## Source Files

- `core/tests/test_fargate_engine.py`

## Audit Trail

- EXTRACTED: 90 (100%)
- INFERRED: 0 (0%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*