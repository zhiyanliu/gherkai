# SSM Path & Client Composition

> 59 nodes · cohesion 0.05

## Key Concepts

- **compose.py** (68 connections) — `runtime/gherkai_runtime/compose.py`
- **WorkerVariantError** (26 connections) — `runtime/gherkai_runtime/compose.py`
- **ssm_path()** (19 connections) — `runtime/gherkai_runtime/names.py`
- **resolve_worker_variant()** (15 connections) — `runtime/gherkai_runtime/compose.py`
- **resolve_default_worker_task_defs()** (14 connections) — `runtime/gherkai_runtime/compose.py`
- **WorkerResolution** (13 connections) — `runtime/gherkai_runtime/compose.py`
- **read_worker_default()** (8 connections) — `runtime/gherkai_runtime/compose.py`
- **_read_worker_image_record()** (8 connections) — `runtime/gherkai_runtime/compose.py`
- **_make_ssm_client()** (7 connections) — `runtime/gherkai_runtime/compose.py`
- **is_botocore_error()** (5 connections) — `runtime/gherkai_runtime/compose.py`
- **_no_default_pointer_error()** (5 connections) — `runtime/gherkai_runtime/compose.py`
- **parse_iso()** (5 connections) — `runtime/gherkai_runtime/compose.py`
- **_release_cmp()** (5 connections) — `runtime/gherkai_runtime/compose.py`
- **_make_ecs_client()** (4 connections) — `runtime/gherkai_runtime/compose.py`
- **_ssm_get()** (4 connections) — `runtime/gherkai_runtime/compose.py`
- **test_read_worker_default_missing_is_none()** (4 connections) — `runtime/tests/test_worker_variant.py`
- **ssm_security_groups_path()** (3 connections) — `deploy_aws/gherkai_deploy_aws/names.py`
- **ssm_subnets_path()** (3 connections) — `deploy_aws/gherkai_deploy_aws/names.py`
- **ssm_version_path()** (3 connections) — `deploy_aws/gherkai_deploy_aws/names.py`
- **_find_worker_spec()** (3 connections) — `runtime/gherkai_runtime/compose.py`
- **is_pure_release()** (3 connections) — `runtime/gherkai_runtime/compose.py`
- **_make_ecr_client()** (3 connections) — `runtime/gherkai_runtime/compose.py`
- **now_iso()** (3 connections) — `runtime/gherkai_runtime/compose.py`
- **_release_key()** (3 connections) — `runtime/gherkai_runtime/compose.py`
- **_variant_miss_hint()** (3 connections) — `runtime/gherkai_runtime/compose.py`
- *... and 34 more nodes in this community*

## Relationships

- [Worker Variant Resolution](Worker_Variant_Resolution.md) (12 shared connections)
- [S3 Report Store & Subprocess](S3_Report_Store_%26_Subprocess.md) (12 shared connections)
- [Cloud Target Resolution](Cloud_Target_Resolution.md) (11 shared connections)
- [Runtime Naming Source](Runtime_Naming_Source.md) (10 shared connections)
- [Run Result Rendering](Run_Result_Rendering.md) (9 shared connections)
- [Cloud Store Composition](Cloud_Store_Composition.md) (7 shared connections)
- [Engine Ports & Adapters](Engine_Ports_%26_Adapters.md) (5 shared connections)
- [Local Run Store](Local_Run_Store.md) (5 shared connections)
- [CDK App & Deploy CLI](CDK_App_%26_Deploy_CLI.md) (4 shared connections)
- [Store Composition & Step Query](Store_Composition_%26_Step_Query.md) (4 shared connections)
- [Backend Version Stamp](Backend_Version_Stamp.md) (4 shared connections)
- [Engine Composition Helpers](Engine_Composition_Helpers.md) (3 shared connections)

## Source Files

- `deploy_aws/gherkai_deploy_aws/names.py`
- `runtime/gherkai_runtime/compose.py`
- `runtime/gherkai_runtime/names.py`
- `runtime/tests/test_compose.py`
- `runtime/tests/test_worker_variant.py`

## Audit Trail

- EXTRACTED: 163 (84%)
- INFERRED: 31 (16%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*