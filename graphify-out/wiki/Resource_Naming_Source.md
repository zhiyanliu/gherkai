# Resource Naming Source

> 29 nodes · cohesion 0.09

## Key Concepts

- **gherkai_runtime/names.py** (16 connections) — `runtime/gherkai_runtime/names.py`
- **image_tag()** (14 connections) — `runtime/gherkai_runtime/names.py`
- **test_names_worker.py** (13 connections) — `runtime/tests/test_names_worker.py`
- **ecr_repo_name()** (7 connections) — `runtime/gherkai_runtime/names.py`
- **default_name()** (6 connections) — `runtime/gherkai_runtime/names.py`
- **task_def_name()** (6 connections) — `runtime/gherkai_runtime/names.py`
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
- **资源命名真源（`gherkai-runtime` 产品本体，ADR 0033「两层命名」）：cli / IaC / Lambda 共用的纯字符串推导。…** (1 connections) — `runtime/gherkai_runtime/names.py`
- **worker 镜像 tag `<归一化版本>-<variant>` —— **命名单一真源，同时是单一校验点**（ADR 0038）。 PEP 440 的…** (1 connections) — `runtime/gherkai_runtime/names.py`
- **镜像 digest 的人读缩写：`sha256:<前 keep 位>`（缺 → `-`）。**单点**：list-workers 表格与 preflight…** (1 connections) — `runtime/gherkai_runtime/names.py`
- **prefix + 基名（原样拼，prefix 含分隔符由用户负责）。CDK 与 cli 共用此推导 → 单一事实源。** (1 connections) — `runtime/gherkai_runtime/names.py`
- **引擎的 task-def family 名：`{prefix}{engine}-worker`（按 job.engine 选，对称…** (1 connections) — `runtime/gherkai_runtime/names.py`
- **job timeout schedule 的名字空间前缀 `{prefix}job-timeout-`（其后接 run+scope 摘要段）。 **含尾部…** (1 connections) — `runtime/gherkai_runtime/names.py`
- **引擎 worker 镜像的 ECR 仓库名 —— **恒等于 `task_def_name(prefix, engine)`**（ADR 0038「tag…** (1 connections) — `runtime/gherkai_runtime/names.py`
- **parametrize** (1 connections)
- **`gherkai_runtime.names` 的 worker 镜像交付命名（ADR 0038「tag 命名 = 单一真源、同时是单一校验点」）。…** (1 connections) — `runtime/tests/test_names_worker.py`
- *... and 4 more nodes in this community*

## Relationships

- [Runtime Composition Root](Runtime_Composition_Root.md) (10 shared connections)
- [Worker Variant Resolution](Worker_Variant_Resolution.md) (7 shared connections)
- [CDK App & AWS Provider CLI](CDK_App_%26_AWS_Provider_CLI.md) (1 shared connections)
- [SQLite Event Log](SQLite_Event_Log.md) (1 shared connections)
- [Cloud Compose Helpers](Cloud_Compose_Helpers.md) (1 shared connections)
- [Cloud Resource Preflight](Cloud_Resource_Preflight.md) (1 shared connections)
- [Cloud Target & Worker Resolution](Cloud_Target_%26_Worker_Resolution.md) (1 shared connections)
- [Backend CDK Stack](Backend_CDK_Stack.md) (1 shared connections)
- [Runtime Composition & Tunnel Host](Runtime_Composition_%26_Tunnel_Host.md) (1 shared connections)

## Source Files

- `runtime/gherkai_runtime/names.py`
- `runtime/tests/test_names_worker.py`

## Audit Trail

- EXTRACTED: 61 (98%)
- INFERRED: 1 (2%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*