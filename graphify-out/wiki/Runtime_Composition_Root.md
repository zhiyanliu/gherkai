# Runtime Composition Root

> 50 nodes · cohesion 0.06

## Key Concepts

- **compose.py** (73 connections) — `runtime/gherkai_runtime/compose.py`
- **WorkerVariantError** (26 connections) — `runtime/gherkai_runtime/compose.py`
- **ssm_path()** (19 connections) — `runtime/gherkai_runtime/names.py`
- **resolve_worker_variant()** (15 connections) — `runtime/gherkai_runtime/compose.py`
- **resolve_default_worker_task_defs()** (14 connections) — `runtime/gherkai_runtime/compose.py`
- **read_worker_default()** (8 connections) — `runtime/gherkai_runtime/compose.py`
- **_read_worker_image_record()** (8 connections) — `runtime/gherkai_runtime/compose.py`
- **worker_image_key()** (8 connections) — `runtime/gherkai_runtime/names.py`
- **_make_ssm_client()** (7 connections) — `runtime/gherkai_runtime/compose.py`
- **parse_iso()** (6 connections) — `runtime/gherkai_runtime/compose.py`
- **run_duration_ms()** (6 connections) — `runtime/gherkai_runtime/compose.py`
- **ssm_worker_template_path()** (5 connections) — `deploy_aws/gherkai_deploy_aws/names.py`
- **is_botocore_error()** (5 connections) — `runtime/gherkai_runtime/compose.py`
- **_no_default_pointer_error()** (5 connections) — `runtime/gherkai_runtime/compose.py`
- **_ssm_get()** (5 connections) — `runtime/gherkai_runtime/compose.py`
- **_make_ecs_client()** (4 connections) — `runtime/gherkai_runtime/compose.py`
- **worker_template_key()** (4 connections) — `runtime/gherkai_runtime/names.py`
- **test_worker_ssm_keys()** (4 connections) — `runtime/tests/test_names_worker.py`
- **test_read_worker_default_missing_is_none()** (4 connections) — `runtime/tests/test_worker_variant.py`
- **_make_ecr_client()** (3 connections) — `runtime/gherkai_runtime/compose.py`
- **test_is_botocore_error_classifies()** (3 connections) — `runtime/tests/test_compose.py`
- **test_run_duration_ms_from_run_state_timestamps()** (3 connections) — `runtime/tests/test_compose.py`
- **_make_lambda_client()** (2 connections) — `runtime/gherkai_runtime/compose.py`
- **new_run_id()** (2 connections) — `runtime/gherkai_runtime/compose.py`
- **probe_aws_identity()** (2 connections) — `runtime/gherkai_runtime/compose.py`
- *... and 25 more nodes in this community*

## Relationships

- [S3 Report Store & Control Plane](S3_Report_Store_%26_Control_Plane.md) (15 shared connections)
- [Cloud Target & Worker Resolution](Cloud_Target_%26_Worker_Resolution.md) (13 shared connections)
- [Worker Variant Resolution](Worker_Variant_Resolution.md) (13 shared connections)
- [Resource Naming Source](Resource_Naming_Source.md) (10 shared connections)
- [SQLite Event Log](SQLite_Event_Log.md) (9 shared connections)
- [Cloud Compose Helpers](Cloud_Compose_Helpers.md) (8 shared connections)
- [CDK App & AWS Provider CLI](CDK_App_%26_AWS_Provider_CLI.md) (5 shared connections)
- [Backend Version Skew Check](Backend_Version_Skew_Check.md) (5 shared connections)
- [Job Explain & S3 Offload](Job_Explain_%26_S3_Offload.md) (5 shared connections)
- [Version Release Comparison](Version_Release_Comparison.md) (4 shared connections)
- [Engine Composition Helpers](Engine_Composition_Helpers.md) (4 shared connections)
- [Deterministic Step Query](Deterministic_Step_Query.md) (3 shared connections)

## Source Files

- `deploy_aws/gherkai_deploy_aws/names.py`
- `runtime/gherkai_runtime/compose.py`
- `runtime/gherkai_runtime/names.py`
- `runtime/tests/test_compose.py`
- `runtime/tests/test_names_worker.py`
- `runtime/tests/test_worker_variant.py`

## Audit Trail

- EXTRACTED: 171 (89%)
- INFERRED: 21 (11%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*