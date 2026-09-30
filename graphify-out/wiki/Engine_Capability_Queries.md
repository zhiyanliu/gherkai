# Engine Capability Queries

> 41 nodes · cohesion 0.06

## Key Concepts

- **query_capabilities()** (17 connections) — `runtime/gherkai_runtime/compose.py`
- **_fake_caps_proc()** (9 connections) — `runtime/tests/test_compose.py`
- **engine_min_grace()** (8 connections) — `runtime/gherkai_runtime/compose.py`
- **match_deterministic()** (7 connections) — `runtime/gherkai_runtime/compose.py`
- **_caps_json()** (7 connections) — `runtime/tests/test_compose.py`
- **test_ask_worker_no_payload_entry_does_not_inherit_stdin()** (6 connections) — `runtime/tests/test_compose.py`
- **test_engine_min_grace_takes_worker_self_reported_value()** (6 connections) — `runtime/tests/test_compose.py`
- **test_query_capabilities_injects_steps_dir_env()** (5 connections) — `runtime/tests/test_compose.py`
- **test_query_capabilities_midscene_gets_no_nova_env()** (5 connections) — `runtime/tests/test_compose.py`
- **test_query_capabilities_rejects_off_contract_answer()** (5 connections) — `runtime/tests/test_compose.py`
- **test_query_capabilities_wrong_engine_names_the_misconfiguration()** (5 connections) — `runtime/tests/test_compose.py`
- **test_chain_level4_skipped_on_non_release_version()** (4 connections) — `runtime/tests/test_compose.py`
- **test_engine_min_grace_reuses_capabilities_asked_with_steps_dir()** (4 connections) — `runtime/tests/test_compose.py`
- **test_engine_min_grace_worker_failure_fails_loud()** (4 connections) — `runtime/tests/test_compose.py`
- **test_query_capabilities_worker_failure_fails_loud_verbatim()** (4 connections) — `runtime/tests/test_compose.py`
- **test_self_describe_miss_raises_worker_not_found()** (4 connections) — `runtime/tests/test_compose.py`
- **test_engine_min_grace_miss_raises_worker_not_found()** (3 connections) — `runtime/tests/test_compose.py`
- **test_query_capabilities_caches_per_engine_and_steps_dir()** (3 connections) — `runtime/tests/test_compose.py`
- **test_query_capabilities_returns_whole_object()** (3 connections) — `runtime/tests/test_compose.py`
- **parametrize** (2 connections)
- **test_engine_min_grace_unknown_engine_raises()** (2 connections) — `runtime/tests/test_compose.py`
- **test_match_deterministic_feeds_stdin_and_parses()** (2 connections) — `runtime/tests/test_compose.py`
- **test_query_capabilities_unknown_engine_raises()** (2 connections) — `runtime/tests/test_compose.py`
- **查某引擎 worker 的能力自述（ADR 0036「5.」）：spawn `worker --capabilities` 收一个 JSON 对象。…** (1 connections) — `runtime/gherkai_runtime/compose.py`
- **批量问某引擎 worker「这些 step 文本各命中哪条确定性模式」（ADR 0036 决策 4，plan 标注用）。 spawn `worker…** (1 connections) — `runtime/gherkai_runtime/compose.py`
- *... and 16 more nodes in this community*

## Relationships

- [Composition Root Helpers](Composition_Root_Helpers.md) (22 shared connections)
- [Cloud Composition Helpers](Cloud_Composition_Helpers.md) (3 shared connections)
- [Worker Self-Describe Spawn](Worker_Self-Describe_Spawn.md) (3 shared connections)
- [CLI Run Wiring Tests](CLI_Run_Wiring_Tests.md) (1 shared connections)

## Source Files

- `runtime/gherkai_runtime/compose.py`
- `runtime/tests/test_compose.py`

## Audit Trail

- EXTRACTED: 81 (99%)
- INFERRED: 1 (1%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*