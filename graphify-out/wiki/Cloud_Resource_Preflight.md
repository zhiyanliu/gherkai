# Cloud Resource Preflight

> 25 nodes · cohesion 0.15

## Key Concepts

- **_FakeEcsClient** (15 connections) — `runtime/tests/test_compose.py`
- **_FakeDdbClient** (14 connections) — `runtime/tests/test_compose.py`
- **_FakeS3Client** (14 connections) — `runtime/tests/test_compose.py`
- **preflight_cloud_resources()** (12 connections) — `runtime/gherkai_runtime/compose.py`
- **_FakeLambdaClient** (10 connections) — `runtime/tests/test_compose.py`
- **_preflight_cap()** (9 connections) — `runtime/tests/test_compose.py`
- **test_preflight_missing_chain_lambda_names_prefix()** (6 connections) — `runtime/tests/test_compose.py`
- **test_preflight_task_defs_and_lambdas_all_present()** (6 connections) — `runtime/tests/test_compose.py`
- **test_preflight_all_present_returns_none()** (5 connections) — `runtime/tests/test_compose.py`
- **test_preflight_missing_cluster_detected()** (5 connections) — `runtime/tests/test_compose.py`
- **test_preflight_missing_events_table_names_prefix()** (5 connections) — `runtime/tests/test_compose.py`
- **test_preflight_missing_task_def_names_prefix()** (5 connections) — `runtime/tests/test_compose.py`
- **test_preflight_no_cap_warn_when_declared_within_cap()** (2 connections) — `runtime/tests/test_compose.py`
- **test_preflight_warns_once_when_declared_max_concurrency_exceeds_cap()** (2 connections) — `runtime/tests/test_compose.py`
- **fail-fast 探 cloud 资源存在性（ADR 0033 preflight 条）——用已解析 prefix 拼出的名去探，不存在返回一句 **点名…** (1 connections) — `runtime/gherkai_runtime/compose.py`
- **.describe_table()** (1 connections) — `runtime/tests/test_compose.py`
- **.__init__()** (1 connections) — `runtime/tests/test_compose.py`
- **.describe_clusters()** (1 connections) — `runtime/tests/test_compose.py`
- **.describe_task_definition()** (1 connections) — `runtime/tests/test_compose.py`
- **.__init__()** (1 connections) — `runtime/tests/test_compose.py`
- **.get_function()** (1 connections) — `runtime/tests/test_compose.py`
- **.__init__()** (1 connections) — `runtime/tests/test_compose.py`
- **.head_bucket()** (1 connections) — `runtime/tests/test_compose.py`
- **.__init__()** (1 connections) — `runtime/tests/test_compose.py`
- **运行一次带 cap 提示的 preflight：推进器 env 给 MAX_CONCURRENCY=cap_env；警告收进 warns。** (1 connections) — `runtime/tests/test_compose.py`

## Relationships

- [Worker Locator & AWS Resolution](Worker_Locator_%26_AWS_Resolution.md) (18 shared connections)
- [Run State Rendering](Run_State_Rendering.md) (8 shared connections)
- [Plan Job Generation](Plan_Job_Generation.md) (4 shared connections)
- [SSM Paths & Composition Root](SSM_Paths_%26_Composition_Root.md) (2 shared connections)
- [Resource Naming Source](Resource_Naming_Source.md) (1 shared connections)

## Source Files

- `runtime/gherkai_runtime/compose.py`
- `runtime/tests/test_compose.py`

## Audit Trail

- EXTRACTED: 65 (84%)
- INFERRED: 12 (16%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*