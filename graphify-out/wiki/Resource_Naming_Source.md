# Resource Naming Source

> 36 nodes · cohesion 0.07

## Key Concepts

- **gherkai_runtime/names.py** (16 connections) — `runtime/gherkai_runtime/names.py`
- **image_tag()** (14 connections) — `runtime/gherkai_runtime/names.py`
- **test_names_worker.py** (13 connections) — `runtime/tests/test_names_worker.py`
- **gherkai_runtime/__init__.py** (10 connections) — `runtime/gherkai_runtime/__init__.py`
- **ecr_repo_name()** (7 connections) — `runtime/gherkai_runtime/names.py`
- **default_name()** (6 connections) — `runtime/gherkai_runtime/names.py`
- **task_def_name()** (6 connections) — `runtime/gherkai_runtime/names.py`
- **ssm_worker_template_path()** (5 connections) — `deploy_aws/gherkai_deploy_aws/names.py`
- **worker_template_key()** (4 connections) — `runtime/gherkai_runtime/names.py`
- **test_worker_ssm_keys()** (4 connections) — `runtime/tests/test_names_worker.py`
- **job_timeout_schedule_prefix()** (3 connections) — `runtime/gherkai_runtime/names.py`
- **test_ecr_repo_name_is_task_def_name()** (3 connections) — `runtime/tests/test_names_worker.py`
- **test_image_tag_rejects_invalid_variant()** (3 connections) — `runtime/tests/test_names_worker.py`
- **test_image_tag_rejects_overlong_tag()** (3 connections) — `runtime/tests/test_names_worker.py`
- **test_image_tag_rejects_version_with_illegal_leading_char()** (3 connections) — `runtime/tests/test_names_worker.py`
- **short_digest()** (2 connections) — `runtime/gherkai_runtime/names.py`
- **test_image_tag_normalizes_epoch()** (2 connections) — `runtime/tests/test_names_worker.py`
- **test_image_tag_normalizes_local_version_segment()** (2 connections) — `runtime/tests/test_names_worker.py`
- **test_image_tag_plain_release()** (2 connections) — `runtime/tests/test_names_worker.py`
- **test_state_worker_task_def_arns_attr_matches_ddb_writer()** (2 connections) — `runtime/tests/test_names_worker.py`
- **引擎 worker task-def **模板 revision ARN** 的 SSM 路径（ADR 0038「SSM 参数与命名真源」第 1 行）。 写者…** (1 connections) — `deploy_aws/gherkai_deploy_aws/names.py`
- **gherkai：产品本体 = 组合根共享层（ADR 0016「演进」节）。 知道产品的一切——引擎注册表与装配（compose）、local…** (1 connections) — `runtime/gherkai_runtime/__init__.py`
- **资源命名真源（`gherkai-runtime` 产品本体，ADR 0033「两层命名」）：cli / IaC / Lambda 共用的纯字符串推导。…** (1 connections) — `runtime/gherkai_runtime/names.py`
- **模板 revision ARN 的 SSM 键（相对键，全路径 = `ssm_path(prefix, 本键)`）。写者 = stack 资源。** (1 connections) — `runtime/gherkai_runtime/names.py`
- **镜像 digest 的人读缩写：`sha256:<前 keep 位>`（缺 → `-`）。**单点**：list-workers 表格与 preflight…** (1 connections) — `runtime/gherkai_runtime/names.py`
- *... and 11 more nodes in this community*

## Relationships

- [Composition Root Wiring](Composition_Root_Wiring.md) (10 shared connections)
- [Worker Variant Resolution](Worker_Variant_Resolution.md) (10 shared connections)
- [CDK App & Deploy CLI](CDK_App_%26_Deploy_CLI.md) (2 shared connections)
- [Worker Image Push Workflow](Worker_Image_Push_Workflow.md) (1 shared connections)
- [CLI Main Entry](CLI_Main_Entry.md) (1 shared connections)
- [CLI Run Entry Tests](CLI_Run_Entry_Tests.md) (1 shared connections)
- [Tunnel CLI Wiring Tests](Tunnel_CLI_Wiring_Tests.md) (1 shared connections)
- [Local Tunnel Exposure](Local_Tunnel_Exposure.md) (1 shared connections)
- [Worker Command Resolution](Worker_Command_Resolution.md) (1 shared connections)
- [Tunnel Host TTL Watchdog](Tunnel_Host_TTL_Watchdog.md) (1 shared connections)
- [Cloud Store Composition](Cloud_Store_Composition.md) (1 shared connections)
- [ADR Index & Dev Docs](ADR_Index_%26_Dev_Docs.md) (1 shared connections)

## Source Files

- `deploy_aws/gherkai_deploy_aws/names.py`
- `runtime/gherkai_runtime/__init__.py`
- `runtime/gherkai_runtime/names.py`
- `runtime/tests/test_names_worker.py`

## Audit Trail

- EXTRACTED: 79 (99%)
- INFERRED: 1 (1%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*