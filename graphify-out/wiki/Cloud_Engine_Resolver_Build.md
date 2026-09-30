# Cloud Engine Resolver Build

> 19 nodes · cohesion 0.11

## Key Concepts

- **build_fargate_engines()** (10 connections) — `runtime/gherkai_runtime/compose.py`
- **_normalize_prefix()** (6 connections) — `runtime/gherkai_runtime/compose.py`
- **_make_ddb_table()** (5 connections) — `runtime/gherkai_runtime/compose.py`
- **make_resolver()** (5 connections) — `runtime/gherkai_runtime/compose.py`
- **_make_s3_client()** (5 connections) — `runtime/gherkai_runtime/compose.py`
- **read_resource()** (4 connections) — `runtime/gherkai_runtime/compose.py`
- **Engine** (3 connections)
- **cloud_artifact_locations()** (3 connections) — `runtime/gherkai_runtime/compose.py`
- **test_worker_task_defs_is_required()** (3 connections) — `runtime/tests/test_worker_variant.py`
- **test_build_fargate_engines_per_engine_taskdef_and_region_no_profile()** (2 connections) — `runtime/tests/test_compose.py`
- **test_engine_absent_from_mapping_gets_throwing_placeholder()** (2 connections) — `runtime/tests/test_worker_variant.py`
- **dict → core 要的 EngineResolver（按 job.engine 取 Engine；未知引擎报错）。** (1 connections) — `runtime/gherkai_runtime/compose.py`
- **云端后端一个 run 的产物落点：jobs_dir / report_index 为 s3://（对拍 S3ResultStore /…** (1 connections) — `runtime/gherkai_runtime/compose.py`
- **S3 key 前缀分隔符规范化：非空且不以 / 结尾则补 /（否则 S3*Store 拼 f'{prefix}{run_id}' 生成粘连 key）。** (1 connections) — `runtime/gherkai_runtime/compose.py`
- **boto3 dynamodb.Table 资源（DDB adapter 吃 resource.Table，非 client）。region/profile 走…** (1 connections) — `runtime/gherkai_runtime/compose.py`
- **boto3 s3 client（三个 S3 件套 ResultStore/ReportStore/offloader 共享同一个）。** (1 connections) — `runtime/gherkai_runtime/compose.py`
- **读一个 `ResourceUri` 的字节（`file://`、裸路径、`s3://`）——**前端层解引用产物 ref 的唯一入口**（ADR 0042…** (1 connections) — `runtime/gherkai_runtime/compose.py`
- **每引擎一个 FargateEngine（对称 build_engines 的 SubprocessEngine dict；core 引擎无关，ADR…** (1 connections) — `runtime/gherkai_runtime/compose.py`
- **漏传 worker_task_defs → TypeError（不静默缺省成 family 名，ADR 0038 不变量做成硬约束）。** (1 connections) — `runtime/tests/test_worker_variant.py`

## Relationships

- [Cloud Composition Helpers](Cloud_Composition_Helpers.md) (8 shared connections)
- [Composition Root Helpers](Composition_Root_Helpers.md) (3 shared connections)
- [S3 Step Argument Offload](S3_Step_Argument_Offload.md) (3 shared connections)
- [Resource Naming and Variants](Resource_Naming_and_Variants.md) (2 shared connections)
- [Tunnel Host Watchdog](Tunnel_Host_Watchdog.md) (1 shared connections)
- [Local Reconcile Rebuild](Local_Reconcile_Rebuild.md) (1 shared connections)
- [Cloud Resource Preflight](Cloud_Resource_Preflight.md) (1 shared connections)
- [Atomic Local Writes](Atomic_Local_Writes.md) (1 shared connections)

## Source Files

- `runtime/gherkai_runtime/compose.py`
- `runtime/tests/test_compose.py`
- `runtime/tests/test_worker_variant.py`

## Audit Trail

- EXTRACTED: 37 (97%)
- INFERRED: 1 (3%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*