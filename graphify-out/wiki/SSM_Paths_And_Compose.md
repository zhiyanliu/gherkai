# SSM Paths And Compose

> 53 nodes · cohesion 0.06

## Key Concepts

- **compose.py** (77 connections) — `runtime/gherkai_runtime/compose.py`
- **ssm_path()** (19 connections) — `runtime/gherkai_runtime/names.py`
- **resolve_worker_variant()** (15 connections) — `runtime/gherkai_runtime/compose.py`
- **resolve_default_worker_task_defs()** (14 connections) — `runtime/gherkai_runtime/compose.py`
- **WorkerResolution** (14 connections) — `runtime/gherkai_runtime/compose.py`
- **gherkai_runtime/__init__.py** (14 connections) — `runtime/gherkai_runtime/__init__.py`
- **tunnel_host.py** (11 connections) — `runtime/gherkai_runtime/tunnel_host.py`
- **read_backend_version()** (10 connections) — `runtime/gherkai_runtime/compose.py`
- **read_worker_default()** (8 connections) — `runtime/gherkai_runtime/compose.py`
- **_read_worker_image_record()** (8 connections) — `runtime/gherkai_runtime/compose.py`
- **check_backend_skew()** (7 connections) — `runtime/gherkai_runtime/compose.py`
- **_make_ssm_client()** (7 connections) — `runtime/gherkai_runtime/compose.py`
- **is_botocore_error()** (5 connections) — `runtime/gherkai_runtime/compose.py`
- **_make_ecs_client()** (5 connections) — `runtime/gherkai_runtime/compose.py`
- **_no_default_pointer_error()** (5 connections) — `runtime/gherkai_runtime/compose.py`
- **_ssm_get()** (5 connections) — `runtime/gherkai_runtime/compose.py`
- **_runtime_version()** (4 connections) — `runtime/gherkai_runtime/compose.py`
- **test_read_worker_default_missing_is_none()** (4 connections) — `runtime/tests/test_worker_variant.py`
- **ssm_security_groups_path()** (3 connections) — `deploy_aws/gherkai_deploy_aws/names.py`
- **ssm_subnets_path()** (3 connections) — `deploy_aws/gherkai_deploy_aws/names.py`
- **ssm_version_path()** (3 connections) — `deploy_aws/gherkai_deploy_aws/names.py`
- **_find_worker_spec()** (3 connections) — `runtime/gherkai_runtime/compose.py`
- **_make_ecr_client()** (3 connections) — `runtime/gherkai_runtime/compose.py`
- **test_is_botocore_error_classifies()** (3 connections) — `runtime/tests/test_compose.py`
- **_make_lambda_client()** (2 connections) — `runtime/gherkai_runtime/compose.py`
- *... and 28 more nodes in this community*

## Relationships

- [AWS Target Resolution](AWS_Target_Resolution.md) (13 shared connections)
- [Worker Variant Resolution](Worker_Variant_Resolution.md) (13 shared connections)
- [Runtime Naming Source](Runtime_Naming_Source.md) (8 shared connections)
- [Store Port Definitions](Store_Port_Definitions.md) (8 shared connections)
- [Cloud Compose Root](Cloud_Compose_Root.md) (8 shared connections)
- [Step Argument S3 Offload](Step_Argument_S3_Offload.md) (7 shared connections)
- [Backend Version Skew Check](Backend_Version_Skew_Check.md) (7 shared connections)
- [Version Skew Check](Version_Skew_Check.md) (6 shared connections)
- [Tunnel Host TTL Daemon](Tunnel_Host_TTL_Daemon.md) (5 shared connections)
- [Worker Capability Probing](Worker_Capability_Probing.md) (5 shared connections)
- [AWS Deploy CLI Provider](AWS_Deploy_CLI_Provider.md) (4 shared connections)
- [Cloud Adapter Boundary Modules](Cloud_Adapter_Boundary_Modules.md) (4 shared connections)

## Source Files

- `deploy_aws/gherkai_deploy_aws/names.py`
- `runtime/gherkai_runtime/__init__.py`
- `runtime/gherkai_runtime/compose.py`
- `runtime/gherkai_runtime/names.py`
- `runtime/gherkai_runtime/tunnel_host.py`
- `runtime/tests/test_compose.py`
- `runtime/tests/test_worker_variant.py`

## Audit Trail

- EXTRACTED: 190 (92%)
- INFERRED: 16 (8%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*