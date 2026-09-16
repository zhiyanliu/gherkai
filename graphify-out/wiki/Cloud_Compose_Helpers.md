# Cloud Compose Helpers

> 18 nodes · cohesion 0.11

## Key Concepts

- **build_fargate_engines()** (11 connections) — `runtime/gherkai_runtime/compose.py`
- **_normalize_prefix()** (6 connections) — `runtime/gherkai_runtime/compose.py`
- **_make_ddb_table()** (5 connections) — `runtime/gherkai_runtime/compose.py`
- **_make_s3_client()** (5 connections) — `runtime/gherkai_runtime/compose.py`
- **read_resource()** (5 connections) — `runtime/gherkai_runtime/compose.py`
- **container_name()** (5 connections) — `runtime/gherkai_runtime/names.py`
- **cloud_artifact_locations()** (3 connections) — `runtime/gherkai_runtime/compose.py`
- **test_worker_task_defs_is_required()** (3 connections) — `runtime/tests/test_worker_variant.py`
- **test_build_fargate_engines_per_engine_taskdef_and_region_no_profile()** (2 connections) — `runtime/tests/test_compose.py`
- **test_engine_absent_from_mapping_gets_throwing_placeholder()** (2 connections) — `runtime/tests/test_worker_variant.py`
- **cloud 档一个 run 的产物落点：jobs_dir / report_index 为 s3://（对拍 S3ResultStore /…** (1 connections) — `runtime/gherkai_runtime/compose.py`
- **S3 key 前缀分隔符规范化：非空且不以 / 结尾则补 /（否则 S3*Store 拼 f'{prefix}{run_id}' 生成粘连 key）。** (1 connections) — `runtime/gherkai_runtime/compose.py`
- **boto3 dynamodb.Table 资源（DDB adapter 吃 resource.Table，非 client）。region/profile 走…** (1 connections) — `runtime/gherkai_runtime/compose.py`
- **boto3 s3 client（三个 S3 件套 ResultStore/ReportStore/offloader 共享同一个）。** (1 connections) — `runtime/gherkai_runtime/compose.py`
- **读一个 `ResourceUri` 的字节（`file://`、裸路径、`s3://`）——**皮层解引用产物 ref 的唯一入口**（ADR 0042…** (1 connections) — `runtime/gherkai_runtime/compose.py`
- **每引擎一个 FargateEngine（对称 build_engines 的 SubprocessEngine dict；core 引擎无关，ADR…** (1 connections) — `runtime/gherkai_runtime/compose.py`
- **task-def 里的 container 名（RunTask overrides 指定往哪个 container 注 env）。不带…** (1 connections) — `runtime/gherkai_runtime/names.py`
- **漏传 worker_task_defs → TypeError（不静默缺省成 family 名，ADR 0038 不变量做成硬约束）。** (1 connections) — `runtime/tests/test_worker_variant.py`

## Relationships

- [Runtime Composition Root](Runtime_Composition_Root.md) (8 shared connections)
- [Job Explain & S3 Offload](Job_Explain_%26_S3_Offload.md) (3 shared connections)
- [Worker Variant Resolution](Worker_Variant_Resolution.md) (3 shared connections)
- [S3 Report Store & Control Plane](S3_Report_Store_%26_Control_Plane.md) (1 shared connections)
- [Tunnel Host Watchdog](Tunnel_Host_Watchdog.md) (1 shared connections)
- [Cloud Resource Preflight](Cloud_Resource_Preflight.md) (1 shared connections)
- [Report Index Collection](Report_Index_Collection.md) (1 shared connections)
- [Backend CDK Stack](Backend_CDK_Stack.md) (1 shared connections)
- [Resource Naming Source](Resource_Naming_Source.md) (1 shared connections)
- [Cloud Target & Worker Resolution](Cloud_Target_%26_Worker_Resolution.md) (1 shared connections)

## Source Files

- `runtime/gherkai_runtime/compose.py`
- `runtime/gherkai_runtime/names.py`
- `runtime/tests/test_compose.py`
- `runtime/tests/test_worker_variant.py`

## Audit Trail

- EXTRACTED: 36 (95%)
- INFERRED: 2 (5%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*