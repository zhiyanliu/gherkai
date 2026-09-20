# Worker Capability Query

> 54 nodes · cohesion 0.05

## Key Concepts

- **query_capabilities()** (17 connections) — `runtime/gherkai_runtime/compose.py`
- **WorkerSelfDescribeError** (15 connections) — `runtime/gherkai_runtime/compose.py`
- **_ask_worker()** (9 connections) — `runtime/gherkai_runtime/compose.py`
- **_fake_caps_proc()** (9 connections) — `runtime/tests/test_compose.py`
- **engine_min_grace()** (8 connections) — `runtime/gherkai_runtime/compose.py`
- **Path** (8 connections)
- **match_deterministic()** (7 connections) — `runtime/gherkai_runtime/compose.py`
- **_caps_json()** (7 connections) — `runtime/tests/test_compose.py`
- **build_local_stores()** (6 connections) — `runtime/gherkai_runtime/compose.py`
- **test_ask_worker_no_payload_entry_does_not_inherit_stdin()** (6 connections) — `runtime/tests/test_compose.py`
- **test_engine_min_grace_takes_worker_self_reported_value()** (6 connections) — `runtime/tests/test_compose.py`
- **test_query_capabilities_injects_steps_dir_env()** (5 connections) — `runtime/tests/test_compose.py`
- **test_query_capabilities_midscene_gets_no_nova_env()** (5 connections) — `runtime/tests/test_compose.py`
- **test_query_capabilities_rejects_off_contract_answer()** (5 connections) — `runtime/tests/test_compose.py`
- **test_query_capabilities_wrong_engine_names_the_misconfiguration()** (5 connections) — `runtime/tests/test_compose.py`
- **RuntimeError** (4 connections)
- **test_chain_level4_skipped_on_non_release_version()** (4 connections) — `runtime/tests/test_compose.py`
- **test_engine_min_grace_reuses_capabilities_asked_with_steps_dir()** (4 connections) — `runtime/tests/test_compose.py`
- **test_engine_min_grace_worker_failure_fails_loud()** (4 connections) — `runtime/tests/test_compose.py`
- **test_query_capabilities_worker_failure_fails_loud_verbatim()** (4 connections) — `runtime/tests/test_compose.py`
- **test_self_describe_miss_raises_worker_not_found()** (4 connections) — `runtime/tests/test_compose.py`
- **local_artifact_locations()** (3 connections) — `runtime/gherkai_runtime/compose.py`
- **.__init__()** (3 connections) — `runtime/gherkai_runtime/compose.py`
- **test_engine_min_grace_miss_raises_worker_not_found()** (3 connections) — `runtime/tests/test_compose.py`
- **test_query_capabilities_caches_per_engine_and_steps_dir()** (3 connections) — `runtime/tests/test_compose.py`
- *... and 29 more nodes in this community*

## Relationships

- [Worker Locator & AWS Resolution](Worker_Locator_%26_AWS_Resolution.md) (22 shared connections)
- [SSM Paths & Composition Root](SSM_Paths_%26_Composition_Root.md) (8 shared connections)
- [Engine Composition Root](Engine_Composition_Root.md) (3 shared connections)
- [S3 Report Store](S3_Report_Store.md) (3 shared connections)
- [Local Report Store](Local_Report_Store.md) (2 shared connections)
- [S3 Result Store Port](S3_Result_Store_Port.md) (2 shared connections)
- [Run State Rendering](Run_State_Rendering.md) (2 shared connections)
- [Local & S3 Result Stores](Local_%26_S3_Result_Stores.md) (1 shared connections)
- [Local Result Store](Local_Result_Store.md) (1 shared connections)
- [Subprocess Engine Launcher](Subprocess_Engine_Launcher.md) (1 shared connections)
- [Plan Job Generation](Plan_Job_Generation.md) (1 shared connections)
- [Run Metadata & S3 Offload](Run_Metadata_%26_S3_Offload.md) (1 shared connections)

## Source Files

- `runtime/gherkai_runtime/compose.py`
- `runtime/tests/test_compose.py`

## Audit Trail

- EXTRACTED: 106 (88%)
- INFERRED: 14 (12%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*