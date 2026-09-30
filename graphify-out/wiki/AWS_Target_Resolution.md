# AWS Target Resolution

> 19 nodes · cohesion 0.12

## Key Concepts

- **resolve_cloud_target()** (11 connections) — `runtime/gherkai_runtime/compose.py`
- **resolve_aws_identity()** (7 connections) — `runtime/gherkai_runtime/compose.py`
- **CloudTarget** (5 connections) — `runtime/gherkai_runtime/compose.py`
- **_clear_aws_env()** (5 connections) — `runtime/tests/test_compose.py`
- **test_resolve_aws_identity_flag_wins_over_env()** (3 connections) — `runtime/tests/test_compose.py`
- **test_resolve_aws_identity_takes_profile_from_env()** (3 connections) — `runtime/tests/test_compose.py`
- **test_resolve_cloud_target_default_prefix_when_nothing_given()** (3 connections) — `runtime/tests/test_compose.py`
- **test_resolve_cloud_target_derives_all_names_from_prefix()** (3 connections) — `runtime/tests/test_compose.py`
- **test_resolve_cloud_target_env_fallbacks_are_deliberately_uneven()** (3 connections) — `runtime/tests/test_compose.py`
- **test_resolve_cloud_target_flags_win_over_env()** (3 connections) — `runtime/tests/test_compose.py`
- **test_resolve_cloud_target_goes_through_resolve_aws_identity()** (3 connections) — `runtime/tests/test_compose.py`
- **.detached_chain_lambdas()** (2 connections) — `runtime/gherkai_runtime/compose.py`
- **AWS 身份解析链的唯一实现：profile 取 flag，缺则取 `AWS_PROFILE`；region 经 `resolve_region`…** (1 connections) — `runtime/gherkai_runtime/compose.py`
- **一次 cloud 调用打到哪儿：prefix + 各资源终名 + region/profile（ADR 0033 两层命名 / 0016 决策 C）。…** (1 connections) — `runtime/gherkai_runtime/compose.py`
- **无状态批量运行事件驱动链的三 Lambda（ADR 0034）——detached submit 的 preflight 名单，顺序即链上顺序。** (1 connections) — `runtime/gherkai_runtime/compose.py`
- **把入口前端已解析的 flag 值解析成 `CloudTarget`（纯字符串推导 + region 落实，不连 AWS）。…** (1 connections) — `runtime/gherkai_runtime/compose.py`
- **profile 入参为 None 时取 `AWS_PROFILE`，并把它喂给 region 解析（profile config 那一级要用它）。** (1 connections) — `runtime/tests/test_compose.py`
- **对偶（防「恒取 env」的假绿反面）：显式 profile 覆盖 `AWS_PROFILE`；显式 region 照样过 resolve_region。** (1 connections) — `runtime/tests/test_compose.py`
- **cloud 目标解析不自写一份身份解析链——换掉唯一实现即整条链改变（单一事实源锁定）。** (1 connections) — `runtime/tests/test_compose.py`

## Relationships

- [Composition Root Helpers](Composition_Root_Helpers.md) (9 shared connections)
- [Cloud Composition Helpers](Cloud_Composition_Helpers.md) (3 shared connections)
- [Worker Log Event Formatting](Worker_Log_Event_Formatting.md) (1 shared connections)
- [Local Reconcile Rebuild](Local_Reconcile_Rebuild.md) (1 shared connections)
- [SSM Path Naming](SSM_Path_Naming.md) (1 shared connections)
- [Tunnel Host Watchdog](Tunnel_Host_Watchdog.md) (1 shared connections)

## Source Files

- `runtime/gherkai_runtime/compose.py`
- `runtime/tests/test_compose.py`

## Audit Trail

- EXTRACTED: 36 (97%)
- INFERRED: 1 (3%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*