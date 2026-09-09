# Cloud Store Composition

> 15 nodes · cohesion 0.15

## Key Concepts

- **build_fargate_engines()** (11 connections) — `runtime/gherkai_runtime/compose.py`
- **build_cloud_stores()** (9 connections) — `runtime/gherkai_runtime/compose.py`
- **_make_ddb_table()** (5 connections) — `runtime/gherkai_runtime/compose.py`
- **_normalize_prefix()** (5 connections) — `runtime/gherkai_runtime/compose.py`
- **container_name()** (5 connections) — `runtime/gherkai_runtime/names.py`
- **_make_s3_client()** (4 connections) — `runtime/gherkai_runtime/compose.py`
- **test_worker_task_defs_is_required()** (3 connections) — `runtime/tests/test_worker_variant.py`
- **test_engine_absent_from_mapping_gets_throwing_placeholder()** (2 connections) — `runtime/tests/test_worker_variant.py`
- **S3 key 前缀分隔符规范化：非空且不以 / 结尾则补 /（否则 S3*Store 拼 f'{prefix}{run_id}' 生成粘连 key）。** (1 connections) — `runtime/gherkai_runtime/compose.py`
- **boto3 dynamodb.Table 资源（DDB adapter 吃 resource.Table，非 client）。region/profile 走…** (1 connections) — `runtime/gherkai_runtime/compose.py`
- **boto3 s3 client（三个 S3 件套 ResultStore/ReportStore/offloader 共享同一个）。** (1 connections) — `runtime/gherkai_runtime/compose.py`
- **云端三层 store（RunStore→DDB、Result/ReportStore→S3）+ cloud artifacts…** (1 connections) — `runtime/gherkai_runtime/compose.py`
- **每引擎一个 FargateEngine（对称 build_engines 的 SubprocessEngine dict；core 引擎无关，ADR…** (1 connections) — `runtime/gherkai_runtime/compose.py`
- **task-def 里的 container 名（RunTask overrides 指定往哪个 container 注 env）。不带…** (1 connections) — `runtime/gherkai_runtime/names.py`
- **漏传 worker_task_defs → TypeError（不静默缺省成 family 名，ADR 0038 不变量做成硬约束）。** (1 connections) — `runtime/tests/test_worker_variant.py`

## Relationships

- [Composition Root Wiring](Composition_Root_Wiring.md) (7 shared connections)
- [Worker Variant Resolution](Worker_Variant_Resolution.md) (3 shared connections)
- [S3 Argument Offload](S3_Argument_Offload.md) (1 shared connections)
- [DynamoDB RunStore Conditional Writes](DynamoDB_RunStore_Conditional_Writes.md) (1 shared connections)
- [S3 ResultStore](S3_ResultStore.md) (1 shared connections)
- [S3 ReportStore & Subprocess Engine](S3_ReportStore_%26_Subprocess_Engine.md) (1 shared connections)
- [Worker Command Resolution](Worker_Command_Resolution.md) (1 shared connections)
- [Run Result Verdict Model](Run_Result_Verdict_Model.md) (1 shared connections)
- [Tunnel Host TTL Watchdog](Tunnel_Host_TTL_Watchdog.md) (1 shared connections)
- [Cloud Resource Preflight Fakes](Cloud_Resource_Preflight_Fakes.md) (1 shared connections)
- [Resource Naming Source](Resource_Naming_Source.md) (1 shared connections)

## Source Files

- `runtime/gherkai_runtime/compose.py`
- `runtime/gherkai_runtime/names.py`
- `runtime/tests/test_worker_variant.py`

## Audit Trail

- EXTRACTED: 31 (89%)
- INFERRED: 4 (11%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*