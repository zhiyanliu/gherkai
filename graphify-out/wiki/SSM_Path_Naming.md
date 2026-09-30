# SSM Path Naming

> 41 nodes · cohesion 0.06

## Key Concepts

- **gherkai_runtime/names.py** (20 connections) — `runtime/gherkai_runtime/names.py`
- **gherkai_deploy_aws/names.py** (17 connections) — `deploy_aws/gherkai_deploy_aws/names.py`
- **image_tag()** (14 connections) — `runtime/gherkai_runtime/names.py`
- **test_names_worker.py** (13 connections) — `runtime/tests/test_names_worker.py`
- **default_name()** (6 connections) — `runtime/gherkai_runtime/names.py`
- **ssm_worker_template_path()** (5 connections) — `deploy_aws/gherkai_deploy_aws/names.py`
- **ssm_vpc_path()** (4 connections) — `deploy_aws/gherkai_deploy_aws/names.py`
- **worker_template_key()** (4 connections) — `runtime/gherkai_runtime/names.py`
- **test_worker_ssm_keys()** (4 connections) — `runtime/tests/test_names_worker.py`
- **ssm_security_groups_path()** (3 connections) — `deploy_aws/gherkai_deploy_aws/names.py`
- **ssm_subnets_path()** (3 connections) — `deploy_aws/gherkai_deploy_aws/names.py`
- **ssm_version_path()** (3 connections) — `deploy_aws/gherkai_deploy_aws/names.py`
- **一个 prefix 即一套环境** (3 connections) — `docs/internals/cloud-backend-carriers.md`
- **job_timeout_schedule_prefix()** (3 connections) — `runtime/gherkai_runtime/names.py`
- **test_image_tag_rejects_invalid_variant()** (3 connections) — `runtime/tests/test_names_worker.py`
- **test_image_tag_rejects_overlong_tag()** (3 connections) — `runtime/tests/test_names_worker.py`
- **test_image_tag_rejects_version_with_illegal_leading_char()** (3 connections) — `runtime/tests/test_names_worker.py`
- **short_digest()** (2 connections) — `runtime/gherkai_runtime/names.py`
- **test_default_name_prefix_original_concat()** (2 connections) — `runtime/tests/test_compose.py`
- **test_image_tag_normalizes_epoch()** (2 connections) — `runtime/tests/test_names_worker.py`
- **test_image_tag_normalizes_local_version_segment()** (2 connections) — `runtime/tests/test_names_worker.py`
- **test_image_tag_plain_release()** (2 connections) — `runtime/tests/test_names_worker.py`
- **test_state_worker_task_def_arns_attr_matches_ddb_writer()** (2 connections) — `runtime/tests/test_names_worker.py`
- **资源命名（ADR 0033 两层命名）——共享部分**直接 import 产品本体 `gherkai_runtime.names`（真同源）**。…** (1 connections) — `deploy_aws/gherkai_deploy_aws/names.py`
- **subnet ID 列表的 SSM 路径（即 gherkai_runtime.names.ssm_path(prefix, SUBNETS_KEY)…** (1 connections) — `deploy_aws/gherkai_deploy_aws/names.py`
- *... and 16 more nodes in this community*

## Relationships

- [Cloud Composition Helpers](Cloud_Composition_Helpers.md) (10 shared connections)
- [Resource Naming and Variants](Resource_Naming_and_Variants.md) (9 shared connections)
- [CDK App & Backend Stack](CDK_App_%26_Backend_Stack.md) (4 shared connections)
- [Worker Image Management](Worker_Image_Management.md) (3 shared connections)
- [Deploy CLI Backend Helpers](Deploy_CLI_Backend_Helpers.md) (2 shared connections)
- [Composition Root Helpers](Composition_Root_Helpers.md) (2 shared connections)
- [Lambda Asset Synth Tests](Lambda_Asset_Synth_Tests.md) (1 shared connections)
- [Deploy Provider Tests](Deploy_Provider_Tests.md) (1 shared connections)
- [CDK Stack Synth Tests](CDK_Stack_Synth_Tests.md) (1 shared connections)
- [Worker Push Deploy Tests](Worker_Push_Deploy_Tests.md) (1 shared connections)
- [Runtime Architecture Concepts](Runtime_Architecture_Concepts.md) (1 shared connections)
- [Local Detached Reconcile](Local_Detached_Reconcile.md) (1 shared connections)

## Source Files

- `deploy_aws/gherkai_deploy_aws/names.py`
- `docs/internals/cloud-backend-carriers.md`
- `runtime/gherkai_runtime/names.py`
- `runtime/tests/test_compose.py`
- `runtime/tests/test_names_worker.py`

## Audit Trail

- EXTRACTED: 90 (99%)
- INFERRED: 1 (1%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*