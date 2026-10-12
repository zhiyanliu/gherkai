# Runtime Naming Source

> 35 nodes · cohesion 0.08

## Key Concepts

- **gherkai_runtime/names.py** (17 connections) — `runtime/gherkai_runtime/names.py`
- **image_tag()** (15 connections) — `runtime/gherkai_runtime/names.py`
- **test_names_worker.py** (13 connections) — `runtime/tests/test_names_worker.py`
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
- **test_default_name_prefix_original_concat()** (2 connections) — `runtime/tests/test_compose.py`
- **test_image_tag_normalizes_epoch()** (2 connections) — `runtime/tests/test_names_worker.py`
- **test_image_tag_normalizes_local_version_segment()** (2 connections) — `runtime/tests/test_names_worker.py`
- **test_image_tag_plain_release()** (2 connections) — `runtime/tests/test_names_worker.py`
- **test_state_worker_task_def_arns_attr_matches_ddb_writer()** (2 connections) — `runtime/tests/test_names_worker.py`
- **引擎 worker task-def **模板 revision ARN** 的 SSM 路径（ADR 0038「SSM 参数与命名真源」第 1 行）。…** (1 connections) — `deploy_aws/gherkai_deploy_aws/names.py`
- **资源命名真源（`gherkai-runtime` 产品本体，ADR 0033「两层命名」）：cli / IaC / Lambda 共用的纯字符串推导。…** (1 connections) — `runtime/gherkai_runtime/names.py`
- **worker 镜像 tag `<归一化版本>-<variant>` —— **命名单一真源，同时是单一校验点**（ADR 0038）。 PEP 440 的…** (1 connections) — `runtime/gherkai_runtime/names.py`
- **模板 revision ARN 的 SSM 键（相对键，全路径为 `ssm_path(prefix, 本键)`）。写者是 stack 资源。** (1 connections) — `runtime/gherkai_runtime/names.py`
- **镜像 digest 的人读缩写：`sha256:<前 keep 位>`（缺 → `-`）。**单点**：list-workers 表格与 preflight…** (1 connections) — `runtime/gherkai_runtime/names.py`
- *... and 10 more nodes in this community*

## Relationships

- [Worker Variant Resolution](Worker_Variant_Resolution.md) (9 shared connections)
- [SSM Paths And Compose](SSM_Paths_And_Compose.md) (8 shared connections)
- [AWS Target Resolution](AWS_Target_Resolution.md) (3 shared connections)
- [AWS Deploy CLI Provider](AWS_Deploy_CLI_Provider.md) (2 shared connections)
- [Task Def Stop Timeout](Task_Def_Stop_Timeout.md) (2 shared connections)
- [AWS Worker Image Registry](AWS_Worker_Image_Registry.md) (1 shared connections)
- [Detached Local Run Host](Detached_Local_Run_Host.md) (1 shared connections)
- [Cloud Resource Preflight](Cloud_Resource_Preflight.md) (1 shared connections)
- [Worker Job Source Input](Worker_Job_Source_Input.md) (1 shared connections)
- [Contributor Docs And ADRs](Contributor_Docs_And_ADRs.md) (1 shared connections)

## Source Files

- `deploy_aws/gherkai_deploy_aws/names.py`
- `runtime/gherkai_runtime/names.py`
- `runtime/tests/test_compose.py`
- `runtime/tests/test_names_worker.py`

## Audit Trail

- EXTRACTED: 73 (99%)
- INFERRED: 1 (1%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*