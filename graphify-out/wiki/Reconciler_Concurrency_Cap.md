# Reconciler Concurrency Cap

> 14 nodes · cohesion 0.14

## Key Concepts

- **_seed_run()** (22 connections) — `deploy_aws/tests/test_lambda_handlers.py`
- **test_reconciler_noop_for_non_detached_run()** (4 connections) — `deploy_aws/tests/test_lambda_handlers.py`
- **test_build_cap_defaults_to_one_when_env_absent()** (3 connections) — `deploy_aws/tests/test_lambda_handlers.py`
- **test_build_clamps_meta_max_concurrency_to_cap()** (3 connections) — `deploy_aws/tests/test_lambda_handlers.py`
- **test_build_defaults_to_one_when_meta_missing()** (3 connections) — `deploy_aws/tests/test_lambda_handlers.py`
- **test_build_raises_when_legacy_definition_unresolvable()** (3 connections) — `deploy_aws/tests/test_lambda_handlers.py`
- **test_build_takes_meta_max_concurrency_under_cap()** (3 connections) — `deploy_aws/tests/test_lambda_handlers.py`
- **建一个单 job、全 pending 的 run（detached 标记按参数）——同 submit / 同步 cloud run 的 create_run…** (1 connections) — `deploy_aws/tests/test_lambda_handlers.py`
- **同步 cloud run 的 events 触发 reconciler → 零 claim / 零 launch / 零 finalize（否则与进程内…** (1 connections) — `deploy_aws/tests/test_lambda_handlers.py`
- **definition 声明 ≤ cap → 按 definition 走（打通前 cloud 档静默忽略提交侧声明，是可用性缺陷）。** (1 connections) — `deploy_aws/tests/test_lambda_handlers.py`
- **definition 声明 > cap → 钳到 cap：task 计入部署方账单，部署侧保留总量控制权（cap 语义）。** (1 connections) — `deploy_aws/tests/test_lambda_handlers.py`
- **meta 无此值（打通前落的旧 definition）→ 按 1，与打通前行为一致（不因 cap 变大把旧 run 提速）。** (1 connections) — `deploy_aws/tests/test_lambda_handlers.py`
- **cap env 漏注（IaC 改坏/手工建的 Lambda）→ 缺省保守回 1，不在 code 里复制部署值。 **meta 必须声明 >1**…** (1 connections) — `deploy_aws/tests/test_lambda_handlers.py`
- **缺字段且 SSM 也解析不出 → 抛，**不回落 family 最新 ACTIVE、不回落模板 revision**（ADR 0038 被拒方案）。** (1 connections) — `deploy_aws/tests/test_lambda_handlers.py`

## Relationships

- [Lambda Handler Event Parsing](Lambda_Handler_Event_Parsing.md) (10 shared connections)
- [Engine Ports & Adapters](Engine_Ports_%26_Adapters.md) (3 shared connections)
- [Worker Task Def Resolution](Worker_Task_Def_Resolution.md) (3 shared connections)
- [Run State Rendering & Boto Guard](Run_State_Rendering_%26_Boto_Guard.md) (2 shared connections)
- [DynamoDB RunStore Conditional Writes](DynamoDB_RunStore_Conditional_Writes.md) (2 shared connections)
- [_stopped_detail](_stopped_detail.md) (2 shared connections)

## Source Files

- `deploy_aws/tests/test_lambda_handlers.py`

## Audit Trail

- EXTRACTED: 35 (100%)
- INFERRED: 0 (0%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*