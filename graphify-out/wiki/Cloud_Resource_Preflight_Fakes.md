# Cloud Resource Preflight Fakes

> 31 nodes · cohesion 0.12

## Key Concepts

- **_FakeEcsClient** (13 connections) — `runtime/tests/test_compose.py`
- **preflight_cloud_resources()** (12 connections) — `runtime/gherkai_runtime/compose.py`
- **_FakeDdbClient** (12 connections) — `runtime/tests/test_compose.py`
- **_FakeS3Client** (12 connections) — `runtime/tests/test_compose.py`
- **_preflight_report_dir()** (11 connections) — `runtime/tests/test_compose.py`
- **_preflight_cap()** (9 connections) — `runtime/tests/test_compose.py`
- **_FakeLambdaClient** (8 connections) — `runtime/tests/test_compose.py`
- **test_preflight_missing_chain_lambda_names_prefix()** (6 connections) — `runtime/tests/test_compose.py`
- **test_preflight_task_defs_and_lambdas_all_present()** (6 connections) — `runtime/tests/test_compose.py`
- **test_preflight_all_present_returns_none()** (5 connections) — `runtime/tests/test_compose.py`
- **test_preflight_missing_cluster_detected()** (5 connections) — `runtime/tests/test_compose.py`
- **test_preflight_missing_events_table_names_prefix()** (5 connections) — `runtime/tests/test_compose.py`
- **test_preflight_missing_task_def_names_prefix()** (5 connections) — `runtime/tests/test_compose.py`
- **test_preflight_no_cap_warn_when_declared_within_cap()** (2 connections) — `runtime/tests/test_compose.py`
- **test_preflight_report_dir_ignores_exit_observer_env()** (2 connections) — `runtime/tests/test_compose.py`
- **test_preflight_report_dir_match_returns_none()** (2 connections) — `runtime/tests/test_compose.py`
- **test_preflight_report_dir_mismatch_detected_when_lambda_env_absent()** (2 connections) — `runtime/tests/test_compose.py`
- **test_preflight_report_dir_mismatch_fails_fast_naming_both_sides()** (2 connections) — `runtime/tests/test_compose.py`
- **test_preflight_report_dir_not_checked_when_not_passed()** (2 connections) — `runtime/tests/test_compose.py`
- **test_preflight_warns_once_when_declared_max_concurrency_exceeds_cap()** (2 connections) — `runtime/tests/test_compose.py`
- **fail-fast 探 cloud 资源存在性（ADR 0033 preflight 条）——用已解析 prefix 拼出的名去探，不存在返回一句 **点名…** (1 connections) — `runtime/gherkai_runtime/compose.py`
- **.describe_table()** (1 connections) — `runtime/tests/test_compose.py`
- **.__init__()** (1 connections) — `runtime/tests/test_compose.py`
- **.describe_clusters()** (1 connections) — `runtime/tests/test_compose.py`
- **.describe_task_definition()** (1 connections) — `runtime/tests/test_compose.py`
- *... and 6 more nodes in this community*

## Relationships

- [Worker Command Resolution](Worker_Command_Resolution.md) (19 shared connections)
- [Feature Planning to Jobs](Feature_Planning_to_Jobs.md) (4 shared connections)
- [Resource Naming Source](Resource_Naming_Source.md) (1 shared connections)
- [Cloud Store Composition](Cloud_Store_Composition.md) (1 shared connections)
- [Composition Root Wiring](Composition_Root_Wiring.md) (1 shared connections)

## Source Files

- `runtime/gherkai_runtime/compose.py`
- `runtime/tests/test_compose.py`

## Audit Trail

- EXTRACTED: 76 (95%)
- INFERRED: 4 (5%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*