# Worker Capability Probing

> 46 nodes · cohesion 0.06

## Key Concepts

- **query_capabilities()** (19 connections) — `runtime/gherkai_runtime/compose.py`
- **_fake_caps_proc()** (9 connections) — `runtime/tests/test_compose.py`
- **engine_min_grace()** (8 connections) — `runtime/gherkai_runtime/compose.py`
- **match_deterministic()** (8 connections) — `runtime/gherkai_runtime/compose.py`
- **Path** (8 connections)
- **_caps_json()** (7 connections) — `runtime/tests/test_compose.py`
- **prune_empty_dirs()** (6 connections) — `runtime/gherkai_runtime/compose.py`
- **test_ask_worker_no_payload_entry_does_not_inherit_stdin()** (6 connections) — `runtime/tests/test_compose.py`
- **test_engine_min_grace_takes_worker_self_reported_value()** (6 connections) — `runtime/tests/test_compose.py`
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
- **test_prune_empty_dirs_keeps_nonempty()** (2 connections) — `runtime/tests/test_compose.py`
- **test_prune_empty_dirs_noop_when_missing()** (2 connections) — `runtime/tests/test_compose.py`
- *... and 21 more nodes in this community*

## Relationships

- [AWS Target Resolution](AWS_Target_Resolution.md) (22 shared connections)
- [SSM Paths And Compose](SSM_Paths_And_Compose.md) (5 shared connections)
- [Store Port Definitions](Store_Port_Definitions.md) (4 shared connections)
- [Nova Act Worker Package](Nova_Act_Worker_Package.md) (2 shared connections)
- [Local Compose Root](Local_Compose_Root.md) (2 shared connections)
- [Run Persistence Local Stores](Run_Persistence_Local_Stores.md) (1 shared connections)
- [Contributor Docs And ADRs](Contributor_Docs_And_ADRs.md) (1 shared connections)
- [Tunnel CLI Wiring Tests](Tunnel_CLI_Wiring_Tests.md) (1 shared connections)

## Source Files

- `runtime/gherkai_runtime/compose.py`
- `runtime/tests/test_compose.py`

## Audit Trail

- EXTRACTED: 94 (97%)
- INFERRED: 3 (3%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*