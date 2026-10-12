# Cloud Store Composition Root

> 61 nodes · cohesion 0.04

## Key Concepts

- **compose.py** (77 connections) — `runtime/gherkai_runtime/compose.py`
- **ssm_path()** (19 connections) — `runtime/gherkai_runtime/names.py`
- **resolve_worker_variant()** (15 connections) — `runtime/gherkai_runtime/compose.py`
- **gherkai_runtime/__init__.py** (14 connections) — `runtime/gherkai_runtime/__init__.py`
- **build_fargate_engines()** (10 connections) — `runtime/gherkai_runtime/compose.py`
- **read_worker_default()** (8 connections) — `runtime/gherkai_runtime/compose.py`
- **_read_worker_image_record()** (8 connections) — `runtime/gherkai_runtime/compose.py`
- **_make_ssm_client()** (7 connections) — `runtime/gherkai_runtime/compose.py`
- **_normalize_prefix()** (6 connections) — `runtime/gherkai_runtime/compose.py`
- **parse_iso()** (6 connections) — `runtime/gherkai_runtime/compose.py`
- **run_duration_ms()** (6 connections) — `runtime/gherkai_runtime/compose.py`
- **ssm_worker_template_path()** (5 connections) — `deploy_aws/gherkai_deploy_aws/names.py`
- **is_botocore_error()** (5 connections) — `runtime/gherkai_runtime/compose.py`
- **_make_ddb_table()** (5 connections) — `runtime/gherkai_runtime/compose.py`
- **_make_ecs_client()** (5 connections) — `runtime/gherkai_runtime/compose.py`
- **_make_s3_client()** (5 connections) — `runtime/gherkai_runtime/compose.py`
- **_no_default_pointer_error()** (5 connections) — `runtime/gherkai_runtime/compose.py`
- **read_resource()** (5 connections) — `runtime/gherkai_runtime/compose.py`
- **_ssm_get()** (5 connections) — `runtime/gherkai_runtime/compose.py`
- **worker_template_key()** (4 connections) — `runtime/gherkai_runtime/names.py`
- **test_worker_ssm_keys()** (4 connections) — `runtime/tests/test_names_worker.py`
- **test_read_worker_default_missing_is_none()** (4 connections) — `runtime/tests/test_worker_variant.py`
- **cloud_artifact_locations()** (3 connections) — `runtime/gherkai_runtime/compose.py`
- **_make_ecr_client()** (3 connections) — `runtime/gherkai_runtime/compose.py`
- **test_is_botocore_error_classifies()** (3 connections) — `runtime/tests/test_compose.py`
- *... and 36 more nodes in this community*

## Relationships

- [Worker Variant Resolution](Worker_Variant_Resolution.md) (17 shared connections)
- [Cloud Launcher & Fargate Adapters](Cloud_Launcher_%26_Fargate_Adapters.md) (15 shared connections)
- [AWS Target & Network Resolution](AWS_Target_%26_Network_Resolution.md) (14 shared connections)
- [SQLite Event Log Adapter](SQLite_Event_Log_Adapter.md) (9 shared connections)
- [Resource Naming Source](Resource_Naming_Source.md) (7 shared connections)
- [Worker Command Resolution Chain](Worker_Command_Resolution_Chain.md) (7 shared connections)
- [CDK App & AWS Provider CLI](CDK_App_%26_AWS_Provider_CLI.md) (5 shared connections)
- [Backend Version Skew Check](Backend_Version_Skew_Check.md) (5 shared connections)
- [Worker Capability Queries](Worker_Capability_Queries.md) (5 shared connections)
- [Job/Scenario Explain Model](Job-Scenario_Explain_Model.md) (4 shared connections)
- [Tunnel Watch TTL Daemon](Tunnel_Watch_TTL_Daemon.md) (3 shared connections)
- [Engine Composition Helpers](Engine_Composition_Helpers.md) (3 shared connections)

## Source Files

- `deploy_aws/gherkai_deploy_aws/names.py`
- `runtime/gherkai_runtime/__init__.py`
- `runtime/gherkai_runtime/compose.py`
- `runtime/gherkai_runtime/names.py`
- `runtime/tests/test_compose.py`
- `runtime/tests/test_names_worker.py`
- `runtime/tests/test_worker_variant.py`

## Audit Trail

- EXTRACTED: 195 (97%)
- INFERRED: 7 (3%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*