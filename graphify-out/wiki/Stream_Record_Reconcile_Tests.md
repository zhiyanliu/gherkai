# Stream Record Reconcile Tests

> 24 nodes · cohesion 0.09

## Key Concepts

- **_stream_record()** (14 connections) — `deploy_aws/tests/test_lambda_handlers.py`
- **test_finished_run_gate_keys_on_the_committed_run_status_only()** (5 connections) — `deploy_aws/tests/test_lambda_handlers.py`
- **test_finished_run_is_not_reprojected_by_a_late_or_replayed_event()** (5 connections) — `deploy_aws/tests/test_lambda_handlers.py`
- **_report_bytes()** (4 connections) — `deploy_aws/tests/test_lambda_handlers.py`
- **test_reconciler_noop_for_non_detached_run()** (4 connections) — `deploy_aws/tests/test_lambda_handlers.py`
- **test_reconciler_writes_timestamps_in_compose_clock_format()** (4 connections) — `deploy_aws/tests/test_lambda_handlers.py`
- **test_timeout_payload_on_a_finished_run_is_a_noop()** (4 connections) — `deploy_aws/tests/test_lambda_handlers.py`
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
- **已收尾的 run 再被触发（迟到重投 / 手工重放同一批 Stream 记录 / TTL 之后的任何唤醒）→ 两个 handler 整体 no-op：判定真值…** (1 connections) — `deploy_aws/tests/test_lambda_handlers.py`
- **对偶（防「闸恒真」的假绿）：闸只认**已提交的 run 级终态**——同一形态（events 只剩退出记录、S3 已有旧产物） 但 run 级仍…** (1 connections) — `deploy_aws/tests/test_lambda_handlers.py`
- **超时到点触发器的 payload 打到一个已收尾的 run（预算点前后跑完的常态）→ 不处置、不改写 （ADR 0034「到点时 job 已终态 → 处置…** (1 connections) — `deploy_aws/tests/test_lambda_handlers.py`
- **推进器 Lambda 落库的时间戳格式 = `compose.now_iso`（三宿主一份时钟，ADR 0034「时钟也只一份」）。 曾在本文件自带…** (1 connections) — `deploy_aws/tests/test_lambda_handlers.py`
- **scope_id 是 @scope 的用户文本、可含 #；run_id 由 compose 生成不含 # → 必须从左切，否则该 run 的整条 events…** (1 connections) — `deploy_aws/tests/test_lambda_handlers.py`

## Relationships

- [Lambda Handler Tests](Lambda_Handler_Tests.md) (14 shared connections)
- [Job Explain & S3 Offload](Job_Explain_%26_S3_Offload.md) (4 shared connections)
- [Detached Run Gates & Concurrency](Detached_Run_Gates_%26_Concurrency.md) (3 shared connections)

## Source Files

- `deploy_aws/tests/test_lambda_handlers.py`

## Audit Trail

- EXTRACTED: 45 (100%)
- INFERRED: 0 (0%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*