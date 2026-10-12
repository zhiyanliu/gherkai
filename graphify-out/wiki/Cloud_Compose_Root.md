# Cloud Compose Root

> 24 nodes · cohesion 0.09

## Key Concepts

- **build_cloud_stores()** (11 connections) — `runtime/gherkai_runtime/compose.py`
- **build_fargate_engines()** (10 connections) — `runtime/gherkai_runtime/compose.py`
- **_normalize_prefix()** (6 connections) — `runtime/gherkai_runtime/compose.py`
- **_make_ddb_table()** (5 connections) — `runtime/gherkai_runtime/compose.py`
- **_make_s3_client()** (5 connections) — `runtime/gherkai_runtime/compose.py`
- **read_resource()** (5 connections) — `runtime/gherkai_runtime/compose.py`
- **_fake_store_ctors()** (5 connections) — `runtime/tests/test_compose.py`
- **test_build_cloud_stores_builds_handles_when_not_injected()** (4 connections) — `runtime/tests/test_compose.py`
- **test_build_cloud_stores_uses_injected_handles_without_building_clients()** (4 connections) — `runtime/tests/test_compose.py`
- **cloud_artifact_locations()** (3 connections) — `runtime/gherkai_runtime/compose.py`
- **test_worker_task_defs_is_required()** (3 connections) — `runtime/tests/test_worker_variant.py`
- **test_build_fargate_engines_per_engine_taskdef_and_region_no_profile()** (2 connections) — `runtime/tests/test_compose.py`
- **test_engine_absent_from_mapping_gets_throwing_placeholder()** (2 connections) — `runtime/tests/test_worker_variant.py`
- **云端后端一个 run 的产物落点：jobs_dir / report_index 为 s3://（对拍 S3ResultStore /…** (1 connections) — `runtime/gherkai_runtime/compose.py`
- **S3 key 前缀分隔符规范化：非空且不以 / 结尾则补 /（否则 S3*Store 拼 f'{prefix}{run_id}' 生成粘连 key）。** (1 connections) — `runtime/gherkai_runtime/compose.py`
- **boto3 dynamodb.Table 资源（DDB adapter 吃 resource.Table，非 client）。region/profile 走…** (1 connections) — `runtime/gherkai_runtime/compose.py`
- **boto3 s3 client（三个 S3 件套 ResultStore/ReportStore/offloader 共享同一个）。** (1 connections) — `runtime/gherkai_runtime/compose.py`
- **云端三层 store（RunStore→DDB、Result/ReportStore→S3）+ cloud artifacts…** (1 connections) — `runtime/gherkai_runtime/compose.py`
- **读一个 `ResourceUri` 的字节（`file://`、裸路径、`s3://`）——**前端层解引用产物 ref 的唯一入口**（ADR 0042…** (1 connections) — `runtime/gherkai_runtime/compose.py`
- **每引擎一个 FargateEngine（对称 build_engines 的 SubprocessEngine dict；core 引擎无关，ADR…** (1 connections) — `runtime/gherkai_runtime/compose.py`
- **不注入则走 _make_* 钩子惰性建（table/region/profile 照传）——注入是可选口子、不改默认路径。** (1 connections) — `runtime/tests/test_compose.py`
- **把 build_cloud_stores 用的四个 adapter 换成只记构造参数的 fake（不 require boto3、不连 AWS）。** (1 connections) — `runtime/tests/test_compose.py`
- **注入 ddb_table/s3 → 原样喂给 store，绝不另建 client（Lambda 组合根靠这条复用它已建的那批句柄，…** (1 connections) — `runtime/tests/test_compose.py`
- **漏传 worker_task_defs → TypeError（不静默缺省成 family 名，ADR 0038 不变量做成硬约束）。** (1 connections) — `runtime/tests/test_worker_variant.py`

## Relationships

- [SSM Paths And Compose](SSM_Paths_And_Compose.md) (8 shared connections)
- [AWS Target Resolution](AWS_Target_Resolution.md) (4 shared connections)
- [Step Argument S3 Offload](Step_Argument_S3_Offload.md) (2 shared connections)
- [Worker Variant Resolution](Worker_Variant_Resolution.md) (2 shared connections)
- [Job Explain Data Model](Job_Explain_Data_Model.md) (1 shared connections)
- [S3 Result Store](S3_Result_Store.md) (1 shared connections)
- [S3 Report Store](S3_Report_Store.md) (1 shared connections)
- [Tunnel Host TTL Daemon](Tunnel_Host_TTL_Daemon.md) (1 shared connections)
- [Cloud Resource Preflight](Cloud_Resource_Preflight.md) (1 shared connections)
- [Report Store Local](Report_Store_Local.md) (1 shared connections)
- [Worker Job Source Input](Worker_Job_Source_Input.md) (1 shared connections)
- [Worker Event Sink](Worker_Event_Sink.md) (1 shared connections)

## Source Files

- `runtime/gherkai_runtime/compose.py`
- `runtime/tests/test_compose.py`
- `runtime/tests/test_worker_variant.py`

## Audit Trail

- EXTRACTED: 43 (86%)
- INFERRED: 7 (14%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*