# Worker Capability Queries

> 43 nodes · cohesion 0.06

## Key Concepts

- **query_capabilities()** (19 connections) — `runtime/gherkai_runtime/compose.py`
- **_ask_worker()** (9 connections) — `runtime/gherkai_runtime/compose.py`
- **_fake_caps_proc()** (9 connections) — `runtime/tests/test_compose.py`
- **engine_min_grace()** (8 connections) — `runtime/gherkai_runtime/compose.py`
- **match_deterministic()** (8 connections) — `runtime/gherkai_runtime/compose.py`
- **Path** (8 connections)
- **_caps_json()** (7 connections) — `runtime/tests/test_compose.py`
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
- **test_query_capabilities_unknown_engine_raises()** (2 connections) — `runtime/tests/test_compose.py`
- **spawn 一次某引擎 worker 的**非 job 入口**、收一行 JSON（ADR 0036「4.」/「5.」两个入口的共同机制）。 非 job…** (1 connections) — `runtime/gherkai_runtime/compose.py`
- *... and 18 more nodes in this community*

## Relationships

- [AWS Target & Network Resolution](AWS_Target_%26_Network_Resolution.md) (19 shared connections)
- [Cloud Store Composition Root](Cloud_Store_Composition_Root.md) (5 shared connections)
- [Cloud Launcher & Fargate Adapters](Cloud_Launcher_%26_Fargate_Adapters.md) (3 shared connections)
- [Worker Command Resolution Chain](Worker_Command_Resolution_Chain.md) (2 shared connections)
- [Nova Act Worker Entry](Nova_Act_Worker_Entry.md) (2 shared connections)
- [Engine Composition Helpers](Engine_Composition_Helpers.md) (2 shared connections)
- [E2E Interrupt Harness](E2E_Interrupt_Harness.md) (1 shared connections)
- [Local Result Store & Persistence](Local_Result_Store_%26_Persistence.md) (1 shared connections)
- [Core Library Concepts & ADRs](Core_Library_Concepts_%26_ADRs.md) (1 shared connections)
- [Local Tunnel Exposure Tests](Local_Tunnel_Exposure_Tests.md) (1 shared connections)

## Source Files

- `runtime/gherkai_runtime/compose.py`
- `runtime/tests/test_compose.py`

## Audit Trail

- EXTRACTED: 91 (96%)
- INFERRED: 4 (4%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*