# Resource Naming Source

> 30 nodes · cohesion 0.09

## Key Concepts

- **gherkai_runtime/names.py** (17 connections) — `runtime/gherkai_runtime/names.py`
- **image_tag()** (14 connections) — `runtime/gherkai_runtime/names.py`
- **test_names_worker.py** (13 connections) — `runtime/tests/test_names_worker.py`
- **default_name()** (6 connections) — `runtime/gherkai_runtime/names.py`
- **ssm_worker_template_path()** (5 connections) — `deploy_aws/gherkai_deploy_aws/names.py`
- **worker_template_key()** (4 connections) — `runtime/gherkai_runtime/names.py`
- **test_worker_ssm_keys()** (4 connections) — `runtime/tests/test_names_worker.py`
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
- **引擎 worker task-def **模板 revision ARN** 的 SSM 路径（ADR 0038「SSM 参数与命名真源」第 1 行）。…** (1 connections) — `deploy_aws/gherkai_deploy_aws/names.py`
- **资源命名真源（`gherkai-runtime` 产品本体，ADR 0033「两层命名」）：cli / IaC / Lambda 共用的纯字符串推导。…** (1 connections) — `runtime/gherkai_runtime/names.py`
- **worker 镜像 tag `<归一化版本>-<variant>` —— **命名单一真源，同时是单一校验点**（ADR 0038）。 PEP 440 的…** (1 connections) — `runtime/gherkai_runtime/names.py`
- **模板 revision ARN 的 SSM 键（相对键，全路径为 `ssm_path(prefix, 本键)`）。写者是 stack 资源。** (1 connections) — `runtime/gherkai_runtime/names.py`
- **镜像 digest 的人读缩写：`sha256:<前 keep 位>`（缺 → `-`）。**单点**：list-workers 表格与 preflight…** (1 connections) — `runtime/gherkai_runtime/names.py`
- **prefix + 基名（原样拼，prefix 含分隔符由部署方负责）。CDK 与 cli 共用此推导 → 单一事实源。** (1 connections) — `runtime/gherkai_runtime/names.py`
- **job timeout schedule 的名字空间前缀 `{prefix}job-timeout-`（其后接 run+scope 摘要段）。 **含尾部…** (1 connections) — `runtime/gherkai_runtime/names.py`
- **parametrize** (1 connections)
- *... and 5 more nodes in this community*

## Relationships

- [Worker Naming & Variants](Worker_Naming_%26_Variants.md) (9 shared connections)
- [SSM Paths & Composition Root](SSM_Paths_%26_Composition_Root.md) (6 shared connections)
- [Worker Locator & AWS Resolution](Worker_Locator_%26_AWS_Resolution.md) (3 shared connections)
- [Deploy CLI Doctor Checks](Deploy_CLI_Doctor_Checks.md) (2 shared connections)
- [AWS Worker Image Management](AWS_Worker_Image_Management.md) (1 shared connections)
- [Local Detached Execution](Local_Detached_Execution.md) (1 shared connections)
- [Task Def Stop Timeout](Task_Def_Stop_Timeout.md) (1 shared connections)
- [Cloud Resource Preflight](Cloud_Resource_Preflight.md) (1 shared connections)
- [Backend CDK Stack](Backend_CDK_Stack.md) (1 shared connections)
- [CLI Test Fixtures](CLI_Test_Fixtures.md) (1 shared connections)

## Source Files

- `deploy_aws/gherkai_deploy_aws/names.py`
- `runtime/gherkai_runtime/names.py`
- `runtime/tests/test_compose.py`
- `runtime/tests/test_names_worker.py`

## Audit Trail

- EXTRACTED: 62 (98%)
- INFERRED: 1 (2%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*