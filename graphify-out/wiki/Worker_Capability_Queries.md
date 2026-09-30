# Worker Capability Queries

> 45 nodes · cohesion 0.06

## Key Concepts

- **query_capabilities()** (17 connections) — `runtime/gherkai_runtime/compose.py`
- **_ask_worker()** (9 connections) — `runtime/gherkai_runtime/compose.py`
- **_fake_caps_proc()** (9 connections) — `runtime/tests/test_compose.py`
- **engine_min_grace()** (8 connections) — `runtime/gherkai_runtime/compose.py`
- **Path** (8 connections)
- **match_deterministic()** (7 connections) — `runtime/gherkai_runtime/compose.py`
- **_caps_json()** (7 connections) — `runtime/tests/test_compose.py`
- **test_ask_worker_no_payload_entry_does_not_inherit_stdin()** (6 connections) — `runtime/tests/test_compose.py`
- **test_engine_min_grace_takes_worker_self_reported_value()** (6 connections) — `runtime/tests/test_compose.py`
- **scrubbed_environ()** (5 connections) — `runtime/gherkai_runtime/compose.py`
- **test_query_capabilities_injects_steps_dir_env()** (5 connections) — `runtime/tests/test_compose.py`
- **test_query_capabilities_midscene_gets_no_nova_env()** (5 connections) — `runtime/tests/test_compose.py`
- **test_query_capabilities_rejects_off_contract_answer()** (5 connections) — `runtime/tests/test_compose.py`
- **test_query_capabilities_wrong_engine_names_the_misconfiguration()** (5 connections) — `runtime/tests/test_compose.py`
- **test_engine_min_grace_reuses_capabilities_asked_with_steps_dir()** (4 connections) — `runtime/tests/test_compose.py`
- **test_engine_min_grace_worker_failure_fails_loud()** (4 connections) — `runtime/tests/test_compose.py`
- **test_query_capabilities_worker_failure_fails_loud_verbatim()** (4 connections) — `runtime/tests/test_compose.py`
- **test_self_describe_miss_raises_worker_not_found()** (4 connections) — `runtime/tests/test_compose.py`
- **local_artifact_locations()** (3 connections) — `runtime/gherkai_runtime/compose.py`
- **test_engine_min_grace_miss_raises_worker_not_found()** (3 connections) — `runtime/tests/test_compose.py`
- **test_query_capabilities_caches_per_engine_and_steps_dir()** (3 connections) — `runtime/tests/test_compose.py`
- **test_query_capabilities_returns_whole_object()** (3 connections) — `runtime/tests/test_compose.py`
- **test_engine_min_grace_unknown_engine_raises()** (2 connections) — `runtime/tests/test_compose.py`
- **test_match_deterministic_feeds_stdin_and_parses()** (2 connections) — `runtime/tests/test_compose.py`
- **test_query_capabilities_unknown_engine_raises()** (2 connections) — `runtime/tests/test_compose.py`
- *... and 20 more nodes in this community*

## Relationships

- [Cloud Resource Resolution](Cloud_Resource_Resolution.md) (21 shared connections)
- [SSM Path Naming](SSM_Path_Naming.md) (6 shared connections)
- [Run Result Aggregation Tree](Run_Result_Aggregation_Tree.md) (3 shared connections)
- [Engine Composition Root](Engine_Composition_Root.md) (3 shared connections)
- [Run Store Adapters](Run_Store_Adapters.md) (1 shared connections)
- [E2E Test Harness](E2E_Test_Harness.md) (1 shared connections)
- [CLI Run Command Tests](CLI_Run_Command_Tests.md) (1 shared connections)

## Source Files

- `runtime/gherkai_runtime/compose.py`
- `runtime/tests/test_compose.py`

## Audit Trail

- EXTRACTED: 95 (99%)
- INFERRED: 1 (1%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*