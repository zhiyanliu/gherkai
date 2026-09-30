# Cloud Composition Helpers

> 62 nodes · cohesion 0.05

## Key Concepts

- **compose.py** (75 connections) — `runtime/gherkai_runtime/compose.py`
- **ssm_path()** (19 connections) — `runtime/gherkai_runtime/names.py`
- **WorkerVariantError** (17 connections) — `runtime/gherkai_runtime/compose.py`
- **resolve_worker_variant()** (15 connections) — `runtime/gherkai_runtime/compose.py`
- **resolve_default_worker_task_defs()** (14 connections) — `runtime/gherkai_runtime/compose.py`
- **read_backend_version()** (10 connections) — `runtime/gherkai_runtime/compose.py`
- **resolve_network()** (9 connections) — `runtime/gherkai_runtime/compose.py`
- **read_worker_default()** (8 connections) — `runtime/gherkai_runtime/compose.py`
- **_read_worker_image_record()** (8 connections) — `runtime/gherkai_runtime/compose.py`
- **check_backend_skew()** (7 connections) — `runtime/gherkai_runtime/compose.py`
- **_make_ssm_client()** (7 connections) — `runtime/gherkai_runtime/compose.py`
- **_UnavailableEngine** (6 connections) — `runtime/gherkai_runtime/compose.py`
- **is_botocore_error()** (5 connections) — `runtime/gherkai_runtime/compose.py`
- **_make_ecs_client()** (5 connections) — `runtime/gherkai_runtime/compose.py`
- **_no_default_pointer_error()** (5 connections) — `runtime/gherkai_runtime/compose.py`
- **_ssm_get()** (5 connections) — `runtime/gherkai_runtime/compose.py`
- **WorkerResolution** (5 connections) — `runtime/gherkai_runtime/compose.py`
- **WorkerCmd** (4 connections) — `runtime/gherkai_runtime/compose.py`
- **test_read_worker_default_missing_is_none()** (4 connections) — `runtime/tests/test_worker_variant.py`
- **_find_worker_spec()** (3 connections) — `runtime/gherkai_runtime/compose.py`
- **local_artifact_locations()** (3 connections) — `runtime/gherkai_runtime/compose.py`
- **_make_ecr_client()** (3 connections) — `runtime/gherkai_runtime/compose.py`
- **_read_ssm_list()** (3 connections) — `runtime/gherkai_runtime/compose.py`
- **test_is_botocore_error_classifies()** (3 connections) — `runtime/tests/test_compose.py`
- **_make_lambda_client()** (2 connections) — `runtime/gherkai_runtime/compose.py`
- *... and 37 more nodes in this community*

## Relationships

- [Composition Root Helpers](Composition_Root_Helpers.md) (15 shared connections)
- [Resource Naming and Variants](Resource_Naming_and_Variants.md) (13 shared connections)
- [SSM Path Naming](SSM_Path_Naming.md) (10 shared connections)
- [Cloud Engine Resolver Build](Cloud_Engine_Resolver_Build.md) (8 shared connections)
- [Version Stamp Skew Check](Version_Stamp_Skew_Check.md) (7 shared connections)
- [Version Skew Checking](Version_Skew_Checking.md) (6 shared connections)
- [Worker Self-Describe Spawn](Worker_Self-Describe_Spawn.md) (5 shared connections)
- [Core Adapters Documentation](Core_Adapters_Documentation.md) (4 shared connections)
- [Worker Log Event Formatting](Worker_Log_Event_Formatting.md) (4 shared connections)
- [Run Duration & Claims](Run_Duration_%26_Claims.md) (3 shared connections)
- [Engine Capability Queries](Engine_Capability_Queries.md) (3 shared connections)
- [AWS Target Resolution](AWS_Target_Resolution.md) (3 shared connections)

## Source Files

- `runtime/gherkai_runtime/compose.py`
- `runtime/gherkai_runtime/names.py`
- `runtime/tests/test_compose.py`
- `runtime/tests/test_worker_variant.py`

## Audit Trail

- EXTRACTED: 184 (92%)
- INFERRED: 15 (8%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*