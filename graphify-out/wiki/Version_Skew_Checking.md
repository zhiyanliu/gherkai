# Version Skew Checking

> 29 nodes · cohesion 0.07

## Key Concepts

- **check_version_skew()** (12 connections) — `runtime/gherkai_runtime/compose.py`
- **_release_cmp()** (6 connections) — `runtime/gherkai_runtime/compose.py`
- **_variant_miss_hint()** (6 connections) — `runtime/gherkai_runtime/compose.py`
- **is_pure_release()** (5 connections) — `runtime/gherkai_runtime/compose.py`
- **_release_key()** (3 connections) — `runtime/gherkai_runtime/compose.py`
- **test_skew_block_when_cli_newer_names_both_exits()** (3 connections) — `runtime/tests/test_compose.py`
- **test_skew_cli_version_is_mandatory_no_runtime_fallback()** (3 connections) — `runtime/tests/test_compose.py`
- **test_skew_compares_release_segment_only()** (3 connections) — `runtime/tests/test_compose.py`
- **test_skew_skip_when_either_side_impure()** (3 connections) — `runtime/tests/test_compose.py`
- **test_skew_skip_when_own_version_unknown()** (3 connections) — `runtime/tests/test_compose.py`
- **test_skew_warn_when_stamp_missing_points_at_deploy()** (3 connections) — `runtime/tests/test_compose.py`
- **test_variant_miss_hint_offers_push_and_base_fallback()** (3 connections) — `runtime/tests/test_compose.py`
- **test_variant_miss_hint_older_cli_only_guides_upgrade()** (3 connections) — `runtime/tests/test_compose.py`
- **test_pure_release_predicate()** (2 connections) — `runtime/tests/test_compose.py`
- **test_skew_ok_same_release_is_silent()** (2 connections) — `runtime/tests/test_compose.py`
- **test_skew_warn_when_cli_older()** (2 connections) — `runtime/tests/test_compose.py`
- **PEP 440 版本的 release 段（`1.4.0.post3+sha` → `(1, 4, 0)`）。 只在 `is_pure_release`…** (1 connections) — `runtime/gherkai_runtime/compose.py`
- **比两个版本的 **release 段**：`a<b` → -1、相等 → 0、`a>b` → 1；**任一侧非纯发行版 → None（无从比较）**。…** (1 connections) — `runtime/gherkai_runtime/compose.py`
- **比 CLI 版本与后端版本戳 → `(verdict, message)`，verdict 取 ok / warn / block / skip 之一（ADR…** (1 connections) — `runtime/gherkai_runtime/compose.py`
- **variant 某一环 miss 时的整句提示——**按版本 skew 分叉**（ADR 0038「preflight」条）。 CLI **旧于**后端（决策…** (1 connections) — `runtime/gherkai_runtime/compose.py`
- **版本是否「纯发行版」（PEP 440：无 .dev / .post / 本地段）——定位链第四级的门槛之一。 dev/post/本地段版本**不可能存在于…** (1 connections) — `runtime/gherkai_runtime/compose.py`
- **CLI 新于后端 → block，且消息必须点名**两条**出路（决策 7 不设放行口，只有这两条）。** (1 connections) — `runtime/tests/test_compose.py`
- **戳缺失表示本机制之前部署的环境 → warn（不拦）+ 提示运行一次 `gherkai deploy` 写入。** (1 connections) — `runtime/tests/test_compose.py`
- **任一侧带 .dev/.post/本地段 → skip（dev 逐提交前进，逐字比会把每次都判成 skew）。** (1 connections) — `runtime/tests/test_compose.py`
- **未装成包（从源码直接运行）→ 调用点取不到自身版本、传 None → skip，不误判成 skew。** (1 connections) — `runtime/tests/test_compose.py`
- *... and 4 more nodes in this community*

## Relationships

- [Worker Locator & AWS Resolution](Worker_Locator_%26_AWS_Resolution.md) (13 shared connections)
- [SSM Paths & Composition Root](SSM_Paths_%26_Composition_Root.md) (6 shared connections)

## Source Files

- `runtime/gherkai_runtime/compose.py`
- `runtime/tests/test_compose.py`

## Audit Trail

- EXTRACTED: 47 (100%)
- INFERRED: 0 (0%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*