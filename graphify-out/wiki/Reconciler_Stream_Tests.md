# Reconciler Stream Tests

> 19 nodes · cohesion 0.11

## Key Concepts

- **_stream_record()** (14 connections) — `deploy_aws/tests/test_lambda_handlers.py`
- **test_reconciler_noop_for_non_detached_run()** (4 connections) — `deploy_aws/tests/test_lambda_handlers.py`
- **test_reconciler_ticks_detached_run()** (4 connections) — `deploy_aws/tests/test_lambda_handlers.py`
- **test_reconciler_writes_timestamps_in_compose_clock_format()** (4 connections) — `deploy_aws/tests/test_lambda_handlers.py`
- **test_run_ids_dedup_multi_scope_same_run()** (3 connections) — `deploy_aws/tests/test_lambda_handlers.py`
- **test_run_ids_keeps_modify_and_records_without_event_name()** (3 connections) — `deploy_aws/tests/test_lambda_handlers.py`
- **test_run_ids_scope_id_containing_hash_is_split_from_the_left()** (3 connections) — `deploy_aws/tests/test_lambda_handlers.py`
- **test_run_ids_scope_with_colon_not_hash()** (3 connections) — `deploy_aws/tests/test_lambda_handlers.py`
- **test_run_ids_skips_ttl_remove_records()** (3 connections) — `deploy_aws/tests/test_lambda_handlers.py`
- **test_run_ids_multi_run()** (2 connections) — `deploy_aws/tests/test_lambda_handlers.py`
- **test_run_ids_single()** (2 connections) — `deploy_aws/tests/test_lambda_handlers.py`
- **同 run 多 scope 的多条 stream record → 去重成一个 run_id（handler 每 run tick 一次）。** (1 connections) — `deploy_aws/tests/test_lambda_handlers.py`
- **events 表 TTL 过期删除同样进 Stream（带 Keys 的 REMOVE 记录）→ 必须不算 run：它不携带新信息，却会让…** (1 connections) — `deploy_aws/tests/test_lambda_handlers.py`
- **只排除 REMOVE、**不做 INSERT 白名单**：events 虽只 PutItem，同键重写（超时处置直写的退出记录被迟到的…** (1 connections) — `deploy_aws/tests/test_lambda_handlers.py`
- **scope_id 含 : （feature:行号）但不含 #——rsplit('#',1) 正确只切 run_id#scope 的分隔。** (1 connections) — `deploy_aws/tests/test_lambda_handlers.py`
- **同步 cloud run 的 events 触发 reconciler → 零 claim / 零 launch / 零 finalize（否则与进程内…** (1 connections) — `deploy_aws/tests/test_lambda_handlers.py`
- **对偶（防「gate 恒真」的假绿）：detached run 照常推进——tick 真实运行、CAS 抢到那个 pending job。** (1 connections) — `deploy_aws/tests/test_lambda_handlers.py`
- **推进器 Lambda 落库的时间戳格式是 `compose.now_iso`（三宿主一份时钟，ADR 0034「时钟也只一份」）。 曾在本文件自带…** (1 connections) — `deploy_aws/tests/test_lambda_handlers.py`
- **scope_id 是 @scope 的用户文本、可含 #；run_id 由 compose 生成不含 # → 必须从左切，否则该 run 的整条 events…** (1 connections) — `deploy_aws/tests/test_lambda_handlers.py`

## Relationships

- [Lambda Handler Tests](Lambda_Handler_Tests.md) (11 shared connections)
- [Run Metadata & S3 Offload](Run_Metadata_%26_S3_Offload.md) (4 shared connections)
- [Finished Run Idempotency](Finished_Run_Idempotency.md) (2 shared connections)

## Source Files

- `deploy_aws/tests/test_lambda_handlers.py`

## Audit Trail

- EXTRACTED: 35 (100%)
- INFERRED: 0 (0%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*