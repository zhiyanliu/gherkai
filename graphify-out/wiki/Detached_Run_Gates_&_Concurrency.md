# Detached Run Gates & Concurrency

> 24 nodes · cohesion 0.09

## Key Concepts

- **_seed_run()** (23 connections) — `deploy_aws/tests/test_lambda_handlers.py`
- **_seed_worker_ssm()** (5 connections) — `deploy_aws/tests/test_lambda_handlers.py`
- **test_build_falls_back_to_default_pointer_for_legacy_definition()** (4 connections) — `deploy_aws/tests/test_lambda_handlers.py`
- **test_build_uses_definition_worker_task_defs_verbatim()** (4 connections) — `deploy_aws/tests/test_lambda_handlers.py`
- **test_kicker_uses_definition_worker_task_defs()** (4 connections) — `deploy_aws/tests/test_lambda_handlers.py`
- **test_reconciler_ticks_detached_run()** (4 connections) — `deploy_aws/tests/test_lambda_handlers.py`
- **test_build_cap_defaults_to_one_when_env_absent()** (3 connections) — `deploy_aws/tests/test_lambda_handlers.py`
- **test_build_clamps_meta_max_concurrency_to_cap()** (3 connections) — `deploy_aws/tests/test_lambda_handlers.py`
- **test_build_defaults_to_one_when_meta_missing()** (3 connections) — `deploy_aws/tests/test_lambda_handlers.py`
- **test_build_raises_when_legacy_definition_unresolvable()** (3 connections) — `deploy_aws/tests/test_lambda_handlers.py`
- **test_build_reuses_its_own_handles_and_builds_no_new_client()** (3 connections) — `deploy_aws/tests/test_lambda_handlers.py`
- **test_build_takes_meta_max_concurrency_under_cap()** (3 connections) — `deploy_aws/tests/test_lambda_handlers.py`
- **建一个单 job、全 pending 的 run（detached 标记按参数）——同 submit / 同步 cloud run 的 create_run…** (1 connections) — `deploy_aws/tests/test_lambda_handlers.py`
- **对偶（防「gate 恒真」的假绿）：detached run 照常推进——tick 真跑、CAS 抢到那个 pending job。** (1 connections) — `deploy_aws/tests/test_lambda_handlers.py`
- **`_build` 的三层 store 全用它自己已建的那批句柄装配——compose 里建句柄的两个钩子在此一次都不该跑。 这条同时是「region 不必传给…** (1 connections) — `deploy_aws/tests/test_lambda_handlers.py`
- **definition 声明 ≤ cap → 按 definition 走（打通前 cloud 档静默忽略提交侧声明，是可用性缺陷）。** (1 connections) — `deploy_aws/tests/test_lambda_handlers.py`
- **definition 声明 > cap → 钳到 cap：task 计入部署方账单，部署侧保留总量控制权（cap 语义）。** (1 connections) — `deploy_aws/tests/test_lambda_handlers.py`
- **meta 无此值（打通前落的旧 definition）→ 按 1，与打通前行为一致（不因 cap 变大把旧 run 提速）。** (1 connections) — `deploy_aws/tests/test_lambda_handlers.py`
- **cap env 漏注（IaC 改坏/手工建的 Lambda）→ 缺省保守回 1，不在 code 里复制部署值。 **meta 必须声明 >1**…** (1 connections) — `deploy_aws/tests/test_lambda_handlers.py`
- **把「后端版本戳 + 默认指针 + (引擎,tag)→revision 映射」落进 moto SSM（= deploy 四步走完的稳态）。** (1 connections) — `deploy_aws/tests/test_lambda_handlers.py`
- **definition 带 worker_task_defs → **原样用**，不看 SSM 默认指针（一个 run 内镜像固定）。 SSM…** (1 connections) — `deploy_aws/tests/test_lambda_handlers.py`
- **definition 缺 worker_task_defs（旧 CLI / 升级前提交）→ 按后端默认指针解析，并点名兼容路径 + variant。** (1 connections) — `deploy_aws/tests/test_lambda_handlers.py`
- **缺字段且 SSM 也解析不出 → 抛，**不回落 family 最新 ACTIVE、不回落模板 revision**（ADR 0038 被拒方案）。** (1 connections) — `deploy_aws/tests/test_lambda_handlers.py`
- **kicker 与 reconciler 共用 `_build` → 同一条解析（不在 kicker 侧另起一套）。** (1 connections) — `deploy_aws/tests/test_lambda_handlers.py`

## Relationships

- [Lambda Handler Tests](Lambda_Handler_Tests.md) (14 shared connections)
- [Job Explain & S3 Offload](Job_Explain_%26_S3_Offload.md) (5 shared connections)
- [Stream Record Reconcile Tests](Stream_Record_Reconcile_Tests.md) (3 shared connections)
- [DynamoDB RunStore Adapter](DynamoDB_RunStore_Adapter.md) (1 shared connections)
- [Run State Rendering](Run_State_Rendering.md) (1 shared connections)

## Source Files

- `deploy_aws/tests/test_lambda_handlers.py`

## Audit Trail

- EXTRACTED: 49 (100%)
- INFERRED: 0 (0%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*