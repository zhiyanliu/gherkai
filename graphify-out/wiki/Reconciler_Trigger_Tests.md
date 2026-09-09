# Reconciler Trigger Tests

> 13 nodes · cohesion 0.15

## Key Concepts

- **_stream_record()** (8 connections) — `deploy_aws/tests/test_lambda_handlers.py`
- **test_reconciler_noop_for_non_detached_run()** (4 connections) — `deploy_aws/tests/test_lambda_handlers.py`
- **test_reconciler_ticks_detached_run()** (4 connections) — `deploy_aws/tests/test_lambda_handlers.py`
- **test_reconciler_writes_timestamps_in_compose_clock_format()** (4 connections) — `deploy_aws/tests/test_lambda_handlers.py`
- **test_run_ids_dedup_multi_scope_same_run()** (3 connections) — `deploy_aws/tests/test_lambda_handlers.py`
- **test_run_ids_scope_with_colon_not_hash()** (3 connections) — `deploy_aws/tests/test_lambda_handlers.py`
- **test_run_ids_multi_run()** (2 connections) — `deploy_aws/tests/test_lambda_handlers.py`
- **test_run_ids_single()** (2 connections) — `deploy_aws/tests/test_lambda_handlers.py`
- **scope_id 含 : （feature:行号）但不含 #——rsplit('#',1) 正确只切 run_id#scope 的分隔。** (1 connections) — `deploy_aws/tests/test_lambda_handlers.py`
- **同步 cloud run 的 events 触发 reconciler → 零 claim / 零 launch / 零 finalize（否则与进程内…** (1 connections) — `deploy_aws/tests/test_lambda_handlers.py`
- **对偶（防「gate 恒真」的假绿）：detached run 照常推进——tick 真跑、CAS 抢到那个 pending job。** (1 connections) — `deploy_aws/tests/test_lambda_handlers.py`
- **推进器 Lambda 落库的时间戳格式 = `compose.now_iso`（三宿主一份时钟，ADR 0034「时钟也只一份」）。 曾在本文件自带…** (1 connections) — `deploy_aws/tests/test_lambda_handlers.py`
- **同 run 多 scope 的多条 stream record → 去重成一个 run_id（handler 每 run tick 一次）。** (1 connections) — `deploy_aws/tests/test_lambda_handlers.py`

## Relationships

- [Lambda Handler Tests](Lambda_Handler_Tests.md) (8 shared connections)
- [Cloud Definition & SSM Tests](Cloud_Definition_%26_SSM_Tests.md) (3 shared connections)

## Source Files

- `deploy_aws/tests/test_lambda_handlers.py`

## Audit Trail

- EXTRACTED: 23 (100%)
- INFERRED: 0 (0%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*