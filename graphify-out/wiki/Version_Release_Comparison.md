# Version Release Comparison

> 13 nodes · cohesion 0.15

## Key Concepts

- **_release_cmp()** (6 connections) — `runtime/gherkai_runtime/compose.py`
- **_variant_miss_hint()** (6 connections) — `runtime/gherkai_runtime/compose.py`
- **is_pure_release()** (5 connections) — `runtime/gherkai_runtime/compose.py`
- **_release_key()** (3 connections) — `runtime/gherkai_runtime/compose.py`
- **test_variant_miss_hint_offers_push_and_base_fallback()** (3 connections) — `runtime/tests/test_compose.py`
- **test_variant_miss_hint_older_cli_only_guides_upgrade()** (3 connections) — `runtime/tests/test_compose.py`
- **test_pure_release_predicate()** (2 connections) — `runtime/tests/test_compose.py`
- **variant 某一环 miss 时的整句提示——**按版本 skew 分叉**（ADR 0038「preflight」条）。 CLI **旧于**后端（决策…** (1 connections) — `runtime/gherkai_runtime/compose.py`
- **版本是否「纯发行版」（PEP 440：无 .dev / .post / 本地段）——定位链第四级的门槛之一。 dev/post/本地段版本**不可能存在于…** (1 connections) — `runtime/gherkai_runtime/compose.py`
- **PEP 440 版本的 release 段（`1.4.0.post3+sha` → `(1, 4, 0)`）。 只在 `is_pure_release`…** (1 connections) — `runtime/gherkai_runtime/compose.py`
- **比两个版本的 **release 段**：`a<b` → -1、相等 → 0、`a>b` → 1；**任一侧非纯发行版 → None（无从比较）**。…** (1 connections) — `runtime/gherkai_runtime/compose.py`
- **同版本档的 variant miss 提示须同时给两条出路（ADR 0038「升级不重置默认指针」条）： 让部署方 push-worker，或临时…** (1 connections) — `runtime/tests/test_compose.py`
- **CLI 旧于后端那一档只引导升级 CLI，不给 push、也不给 base 兜底（推旧命名空间的 tag 是原地绕圈）。** (1 connections) — `runtime/tests/test_compose.py`

## Relationships

- [Cloud Target & Worker Resolution](Cloud_Target_%26_Worker_Resolution.md) (5 shared connections)
- [Runtime Composition Root](Runtime_Composition_Root.md) (4 shared connections)
- [Version Skew Check](Version_Skew_Check.md) (1 shared connections)

## Source Files

- `runtime/gherkai_runtime/compose.py`
- `runtime/tests/test_compose.py`

## Audit Trail

- EXTRACTED: 22 (100%)
- INFERRED: 0 (0%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*