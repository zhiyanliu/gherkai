# Cloud Target Resolution

> 14 nodes · cohesion 0.18

## Key Concepts

- **resolve_cloud_target()** (10 connections) — `runtime/gherkai_runtime/compose.py`
- **resolve_region()** (9 connections) — `runtime/gherkai_runtime/compose.py`
- **_clear_aws_env()** (5 connections) — `runtime/tests/test_compose.py`
- **test_resolve_cloud_target_default_prefix_when_nothing_given()** (3 connections) — `runtime/tests/test_compose.py`
- **test_resolve_cloud_target_derives_all_names_from_prefix()** (3 connections) — `runtime/tests/test_compose.py`
- **test_resolve_cloud_target_env_fallbacks_are_deliberately_uneven()** (3 connections) — `runtime/tests/test_compose.py`
- **test_resolve_cloud_target_flags_win_over_env()** (3 connections) — `runtime/tests/test_compose.py`
- **test_resolve_region_env_chain()** (2 connections) — `runtime/tests/test_compose.py`
- **test_resolve_region_explicit_wins()** (2 connections) — `runtime/tests/test_compose.py`
- **test_resolve_region_falls_back_to_profile_config()** (2 connections) — `runtime/tests/test_compose.py`
- **test_resolve_region_no_boto3_returns_none_not_crash()** (2 connections) — `runtime/tests/test_compose.py`
- **test_resolve_region_none_when_all_miss()** (2 connections) — `runtime/tests/test_compose.py`
- **把 region 解析成**具体字符串**（ADR 0016 决策 C）：--region > AWS_REGION > AWS_DEFAULT_REGION…** (1 connections) — `runtime/gherkai_runtime/compose.py`
- **把入口皮已解析的 flag 值解析成 `CloudTarget`（纯字符串推导 + region 落实，不连 AWS）。…** (1 connections) — `runtime/gherkai_runtime/compose.py`

## Relationships

- [Worker Command Resolution](Worker_Command_Resolution.md) (10 shared connections)
- [Composition Root Wiring](Composition_Root_Wiring.md) (2 shared connections)
- [Resource Naming Source](Resource_Naming_Source.md) (1 shared connections)
- [Tunnel Host TTL Watchdog](Tunnel_Host_TTL_Watchdog.md) (1 shared connections)
- [S3 ReportStore & Subprocess Engine](S3_ReportStore_%26_Subprocess_Engine.md) (1 shared connections)
- [Detached Launcher Reconcile](Detached_Launcher_Reconcile.md) (1 shared connections)

## Source Files

- `runtime/gherkai_runtime/compose.py`
- `runtime/tests/test_compose.py`

## Audit Trail

- EXTRACTED: 32 (100%)
- INFERRED: 0 (0%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*