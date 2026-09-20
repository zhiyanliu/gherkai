# SSM Paths & Composition Root

> 63 nodes · cohesion 0.05

## Key Concepts

- **compose.py** (73 connections) — `runtime/gherkai_runtime/compose.py`
- **WorkerVariantError** (26 connections) — `runtime/gherkai_runtime/compose.py`
- **ssm_path()** (19 connections) — `runtime/gherkai_runtime/names.py`
- **resolve_worker_variant()** (15 connections) — `runtime/gherkai_runtime/compose.py`
- **resolve_default_worker_task_defs()** (14 connections) — `runtime/gherkai_runtime/compose.py`
- **WorkerResolution** (14 connections) — `runtime/gherkai_runtime/compose.py`
- **build_fargate_engines()** (10 connections) — `runtime/gherkai_runtime/compose.py`
- **read_backend_version()** (10 connections) — `runtime/gherkai_runtime/compose.py`
- **read_worker_default()** (8 connections) — `runtime/gherkai_runtime/compose.py`
- **_read_worker_image_record()** (8 connections) — `runtime/gherkai_runtime/compose.py`
- **check_backend_skew()** (7 connections) — `runtime/gherkai_runtime/compose.py`
- **_make_ssm_client()** (7 connections) — `runtime/gherkai_runtime/compose.py`
- **_normalize_prefix()** (6 connections) — `runtime/gherkai_runtime/compose.py`
- **is_botocore_error()** (5 connections) — `runtime/gherkai_runtime/compose.py`
- **_make_ddb_table()** (5 connections) — `runtime/gherkai_runtime/compose.py`
- **_make_ecs_client()** (5 connections) — `runtime/gherkai_runtime/compose.py`
- **_make_s3_client()** (5 connections) — `runtime/gherkai_runtime/compose.py`
- **_no_default_pointer_error()** (5 connections) — `runtime/gherkai_runtime/compose.py`
- **read_resource()** (5 connections) — `runtime/gherkai_runtime/compose.py`
- **_ssm_get()** (5 connections) — `runtime/gherkai_runtime/compose.py`
- **test_read_worker_default_missing_is_none()** (4 connections) — `runtime/tests/test_worker_variant.py`
- **ssm_security_groups_path()** (3 connections) — `deploy_aws/gherkai_deploy_aws/names.py`
- **ssm_subnets_path()** (3 connections) — `deploy_aws/gherkai_deploy_aws/names.py`
- **ssm_version_path()** (3 connections) — `deploy_aws/gherkai_deploy_aws/names.py`
- **cloud_artifact_locations()** (3 connections) — `runtime/gherkai_runtime/compose.py`
- *... and 38 more nodes in this community*

## Relationships

- [Worker Naming & Variants](Worker_Naming_%26_Variants.md) (15 shared connections)
- [Worker Locator & AWS Resolution](Worker_Locator_%26_AWS_Resolution.md) (14 shared connections)
- [Run Metadata & S3 Offload](Run_Metadata_%26_S3_Offload.md) (10 shared connections)
- [Worker Capability Query](Worker_Capability_Query.md) (8 shared connections)
- [Backend Version Skew Check](Backend_Version_Skew_Check.md) (7 shared connections)
- [S3 Result Store Port](S3_Result_Store_Port.md) (6 shared connections)
- [Resource Naming Source](Resource_Naming_Source.md) (6 shared connections)
- [Version Skew Checking](Version_Skew_Checking.md) (6 shared connections)
- [S3 Report Store](S3_Report_Store.md) (5 shared connections)
- [Deploy CLI Doctor Checks](Deploy_CLI_Doctor_Checks.md) (4 shared connections)
- [Timestamps & Wallclock](Timestamps_%26_Wallclock.md) (4 shared connections)
- [Engine Composition Root](Engine_Composition_Root.md) (4 shared connections)

## Source Files

- `deploy_aws/gherkai_deploy_aws/names.py`
- `runtime/gherkai_runtime/compose.py`
- `runtime/gherkai_runtime/names.py`
- `runtime/tests/test_compose.py`
- `runtime/tests/test_worker_variant.py`

## Audit Trail

- EXTRACTED: 189 (85%)
- INFERRED: 33 (15%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*