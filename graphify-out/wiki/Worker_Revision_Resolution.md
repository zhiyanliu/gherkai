# Worker Revision Resolution

> 8 nodes · cohesion 0.25

## Key Concepts

- **_seed_worker_ssm()** (5 connections) — `deploy_aws/tests/test_lambda_handlers.py`
- **test_build_falls_back_to_default_pointer_for_legacy_definition()** (4 connections) — `deploy_aws/tests/test_lambda_handlers.py`
- **test_build_uses_definition_worker_task_defs_verbatim()** (4 connections) — `deploy_aws/tests/test_lambda_handlers.py`
- **test_kicker_uses_definition_worker_task_defs()** (4 connections) — `deploy_aws/tests/test_lambda_handlers.py`
- **把「后端版本戳 + 默认指针 + (引擎,tag)→revision 映射」落进 moto SSM（即 deploy 四步走完的稳态）。** (1 connections) — `deploy_aws/tests/test_lambda_handlers.py`
- **definition 带 worker_task_defs → **原样用**，不看 SSM 默认指针（一个 run 内镜像固定）。 SSM…** (1 connections) — `deploy_aws/tests/test_lambda_handlers.py`
- **definition 缺 worker_task_defs（旧 CLI / 升级前提交）→ 按后端默认指针解析，并点名兼容路径 + variant。** (1 connections) — `deploy_aws/tests/test_lambda_handlers.py`
- **kicker 与 reconciler 共用 `_build` → 同一条解析（不在 kicker 侧另起一套）。** (1 connections) — `deploy_aws/tests/test_lambda_handlers.py`

## Relationships

- [Lambda Handler Tests](Lambda_Handler_Tests.md) (4 shared connections)
- [Run Metadata & S3 Offload](Run_Metadata_%26_S3_Offload.md) (3 shared connections)

## Source Files

- `deploy_aws/tests/test_lambda_handlers.py`

## Audit Trail

- EXTRACTED: 14 (100%)
- INFERRED: 0 (0%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*