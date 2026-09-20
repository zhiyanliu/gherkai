# Finished Run Idempotency

> 7 nodes · cohesion 0.29

## Key Concepts

- **test_finished_run_gate_keys_on_the_committed_run_status_only()** (5 connections) — `deploy_aws/tests/test_lambda_handlers.py`
- **test_finished_run_is_not_reprojected_by_a_late_or_replayed_event()** (5 connections) — `deploy_aws/tests/test_lambda_handlers.py`
- **_report_bytes()** (4 connections) — `deploy_aws/tests/test_lambda_handlers.py`
- **test_timeout_payload_on_a_finished_run_is_a_noop()** (4 connections) — `deploy_aws/tests/test_lambda_handlers.py`
- **已收尾的 run 再被触发（迟到重投 / 手工重放同一批 Stream 记录 / TTL 之后的任何唤醒）→ 两个 handler 整体 no-op：判定真值…** (1 connections) — `deploy_aws/tests/test_lambda_handlers.py`
- **对偶（防「闸恒真」的假绿）：闸只认**已提交的 run 级终态**——同一形态（events 只剩退出记录、S3 已有旧产物） 但 run 级仍…** (1 connections) — `deploy_aws/tests/test_lambda_handlers.py`
- **超时到点触发器的 payload 打到一个已收尾的 run（预算点前后运行结束的常态）→ 不处置、不改写 （ADR 0034「到点时 job 已终态 → 处置…** (1 connections) — `deploy_aws/tests/test_lambda_handlers.py`

## Relationships

- [Lambda Handler Tests](Lambda_Handler_Tests.md) (4 shared connections)
- [Run Metadata & S3 Offload](Run_Metadata_%26_S3_Offload.md) (3 shared connections)
- [Reconciler Stream Tests](Reconciler_Stream_Tests.md) (2 shared connections)

## Source Files

- `deploy_aws/tests/test_lambda_handlers.py`

## Audit Trail

- EXTRACTED: 15 (100%)
- INFERRED: 0 (0%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*