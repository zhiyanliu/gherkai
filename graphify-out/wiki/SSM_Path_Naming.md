# SSM Path Naming

> 64 nodes · cohesion 0.05

## Key Concepts

- **compose.py** (72 connections) — `runtime/gherkai_runtime/compose.py`
- **WorkerVariantError** (26 connections) — `runtime/gherkai_runtime/compose.py`
- **ssm_path()** (19 connections) — `runtime/gherkai_runtime/names.py`
- **resolve_worker_variant()** (15 connections) — `runtime/gherkai_runtime/compose.py`
- **resolve_default_worker_task_defs()** (14 connections) — `runtime/gherkai_runtime/compose.py`
- **build_fargate_engines()** (10 connections) — `runtime/gherkai_runtime/compose.py`
- **read_worker_default()** (8 connections) — `runtime/gherkai_runtime/compose.py`
- **_read_worker_image_record()** (8 connections) — `runtime/gherkai_runtime/compose.py`
- **worker_image_key()** (8 connections) — `runtime/gherkai_runtime/names.py`
- **_make_ssm_client()** (7 connections) — `runtime/gherkai_runtime/compose.py`
- **_normalize_prefix()** (6 connections) — `runtime/gherkai_runtime/compose.py`
- **ssm_worker_template_path()** (5 connections) — `deploy_aws/gherkai_deploy_aws/names.py`
- **_make_ddb_table()** (5 connections) — `runtime/gherkai_runtime/compose.py`
- **_make_ecs_client()** (5 connections) — `runtime/gherkai_runtime/compose.py`
- **_make_s3_client()** (5 connections) — `runtime/gherkai_runtime/compose.py`
- **_no_default_pointer_error()** (5 connections) — `runtime/gherkai_runtime/compose.py`
- **read_resource()** (5 connections) — `runtime/gherkai_runtime/compose.py`
- **_ssm_get()** (5 connections) — `runtime/gherkai_runtime/compose.py`
- **worker_template_key()** (4 connections) — `runtime/gherkai_runtime/names.py`
- **test_worker_ssm_keys()** (4 connections) — `runtime/tests/test_names_worker.py`
- **test_read_worker_default_missing_is_none()** (4 connections) — `runtime/tests/test_worker_variant.py`
- **ssm_security_groups_path()** (3 connections) — `deploy_aws/gherkai_deploy_aws/names.py`
- **ssm_subnets_path()** (3 connections) — `deploy_aws/gherkai_deploy_aws/names.py`
- **ssm_version_path()** (3 connections) — `deploy_aws/gherkai_deploy_aws/names.py`
- **cloud_artifact_locations()** (3 connections) — `runtime/gherkai_runtime/compose.py`
- *... and 39 more nodes in this community*

## Relationships

- [Run Result Aggregation Tree](Run_Result_Aggregation_Tree.md) (16 shared connections)
- [Worker Variant Resolution](Worker_Variant_Resolution.md) (15 shared connections)
- [Cloud Resource Resolution](Cloud_Resource_Resolution.md) (12 shared connections)
- [Resource Naming Source](Resource_Naming_Source.md) (8 shared connections)
- [Worker Capability Queries](Worker_Capability_Queries.md) (6 shared connections)
- [CDK App and Deploy CLI](CDK_App_and_Deploy_CLI.md) (5 shared connections)
- [Backend Version Stamp](Backend_Version_Stamp.md) (5 shared connections)
- [Version Skew Check](Version_Skew_Check.md) (5 shared connections)
- [S3 Store Adapters](S3_Store_Adapters.md) (5 shared connections)
- [Wall Clock Timestamps](Wall_Clock_Timestamps.md) (4 shared connections)
- [Job Domain Models](Job_Domain_Models.md) (4 shared connections)
- [Release Notes Tooling](Release_Notes_Tooling.md) (4 shared connections)

## Source Files

- `deploy_aws/gherkai_deploy_aws/names.py`
- `runtime/gherkai_runtime/compose.py`
- `runtime/gherkai_runtime/names.py`
- `runtime/tests/test_compose.py`
- `runtime/tests/test_names_worker.py`
- `runtime/tests/test_worker_variant.py`

## Audit Trail

- EXTRACTED: 190 (90%)
- INFERRED: 21 (10%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*