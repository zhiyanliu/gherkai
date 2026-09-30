# Fargate Engine Tests

> 23 nodes · cohesion 0.13

## Key Concepts

- **test_fargate_engine.py** (76 connections) — `core/tests/test_fargate_engine.py`
- **_spy_run_task_env()** (9 connections) — `core/tests/test_fargate_engine.py`
- **_await_engine()** (6 connections) — `core/tests/test_fargate_engine.py`
- **_stopped_resp()** (4 connections) — `core/tests/test_fargate_engine.py`
- **test_await_exit_code_null_beyond_grace_settles_as_error()** (3 connections) — `core/tests/test_fargate_engine.py`
- **test_await_exit_code_null_then_nonzero_landed_preserved()** (3 connections) — `core/tests/test_fargate_engine.py`
- **test_await_exit_code_waits_out_null_then_reads_landed_code()** (3 connections) — `core/tests/test_fargate_engine.py`
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
- **FargateEngine adapter 单测（ADR 0024「DynamoDB 作 events-out」）。…** (1 connections) — `core/tests/test_fargate_engine.py`
- **_final_drain 终读须翻页：>1MB 尾部 DDB Query 分页返回 LastEvaluatedKey，不循环…** (1 connections) — `core/tests/test_fargate_engine.py`
- **码→异常的翻译已收进 `wire`（协议级、与 subprocess adapter 共用一份）：这里锁本 adapter 的调法…** (1 connections) — `core/tests/test_fargate_engine.py`
- **终读是强一致读，其中的断号无从补、只记警告（不等、不停）。** (1 connections) — `core/tests/test_fargate_engine.py`
- **MISSING 只是瞬时（最终一致）→ 宽限内恢复可见并 STOPPED → 正常读到码，不误报。** (1 connections) — `core/tests/test_fargate_engine.py`
- **执行 run_scope、拦 run_task 抓 overrides env → 返回 {name: value} dict。** (1 connections) — `core/tests/test_fargate_engine.py`

## Relationships

- [Worker Exit Drain Tests](Worker_Exit_Drain_Tests.md) (29 shared connections)
- [Event Gap Grace Tests](Event_Gap_Grace_Tests.md) (8 shared connections)
- [ECS Task Exit Probing](ECS_Task_Exit_Probing.md) (7 shared connections)
- [Fargate Engine Adapter](Fargate_Engine_Adapter.md) (4 shared connections)
- [Fargate Worker Handle](Fargate_Worker_Handle.md) (3 shared connections)
- [Worker Log Event Formatting](Worker_Log_Event_Formatting.md) (3 shared connections)
- [Run Definition Domain Model](Run_Definition_Domain_Model.md) (3 shared connections)
- [Core Adapters Documentation](Core_Adapters_Documentation.md) (3 shared connections)
- [Event Keys & Exit Records](Event_Keys_%26_Exit_Records.md) (2 shared connections)
- [Event Wire Serialization](Event_Wire_Serialization.md) (2 shared connections)
- [Event Sequence Gap Handling](Event_Sequence_Gap_Handling.md) (2 shared connections)
- [Event Records Projection](Event_Records_Projection.md) (1 shared connections)

## Source Files

- `core/tests/test_fargate_engine.py`

## Audit Trail

- EXTRACTED: 103 (100%)
- INFERRED: 0 (0%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*