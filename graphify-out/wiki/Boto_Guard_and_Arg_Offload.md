# Boto Guard and Arg Offload

> 33 nodes · cohesion 0.08

## Key Concepts

- **S3StepArgumentOffloader** (27 connections) — `core/gherkai_core/adapters/run_store/arg_offload.py`
- **require_boto3()** (14 connections) — `core/gherkai_core/adapters/_boto.py`
- **_boto.py** (8 connections) — `core/gherkai_core/adapters/_boto.py`
- **arg_offload.py** (7 connections) — `core/gherkai_core/adapters/run_store/arg_offload.py`
- **has_pointers()** (5 connections) — `core/gherkai_core/adapters/run_store/arg_offload.py`
- **_iter_arguments()** (5 connections) — `core/gherkai_core/adapters/run_store/arg_offload.py`
- **.offload()** (5 connections) — `core/gherkai_core/adapters/run_store/arg_offload.py`
- **.load_run_meta()** (5 connections) — `core/gherkai_core/adapters/run_store/ddb.py`
- **.restore()** (4 connections) — `core/gherkai_core/adapters/run_store/arg_offload.py`
- **arg_offloader()** (4 connections) — `core/tests/conftest.py`
- **.__init__()** (3 connections) — `core/gherkai_core/adapters/report_store/s3.py`
- **.__init__()** (3 connections) — `core/gherkai_core/adapters/result_store/s3.py`
- **._fetch()** (3 connections) — `core/gherkai_core/adapters/run_store/arg_offload.py`
- **.__init__()** (3 connections) — `core/gherkai_core/adapters/run_store/arg_offload.py`
- **._put()** (3 connections) — `core/gherkai_core/adapters/run_store/arg_offload.py`
- **.__init__()** (3 connections) — `core/gherkai_core/adapters/run_store/ddb.py`
- **._key()** (2 connections) — `core/gherkai_core/adapters/run_store/arg_offload.py`
- **云端 adapter 共享的 boto3 依赖守卫（ADR 0016 窄腰 / 0030 决定六方案 A）。 凡走 `aws` extra 的 adapter…** (1 connections) — `core/gherkai_core/adapters/_boto.py`
- **缺 boto3 时抛带组件名的友好 ImportError（`pip install 'gherkai-core[aws]'`）；模块 import…** (1 connections) — `core/gherkai_core/adapters/_boto.py`
- **s3_client：boto3 s3 client（组合根注入；建桶责任在 IaC，adapter 假定桶已存在）。 prefix：可选 key 前缀（如…** (1 connections) — `core/gherkai_core/adapters/report_store/s3.py`
- **s3_client：boto3 s3 client（组合根注入；建桶责任在 IaC，adapter 假定桶已存在）。 prefix：可选 key 前缀（如…** (1 connections) — `core/gherkai_core/adapters/result_store/s3.py`
- **StepArgument S3 offload（ADR 0030 决定六）：把 RunMeta 深树里的 docString/dataTable 换成 S3…** (1 connections) — `core/gherkai_core/adapters/run_store/arg_offload.py`
- **按 s3:// URI 取回 JSON 值（解析出 bucket/key，不重算——URI 自描述）。** (1 connections) — `core/gherkai_core/adapters/run_store/arg_offload.py`
- **遍历 run_meta_to_dict 产物里每个带 argument 的 step，yield (arg_dict, scope_id,…** (1 connections) — `core/gherkai_core/adapters/run_store/arg_offload.py`
- **meta_dict 里是否存在 offload 指针（`content_ref`/`rows_ref`）——**按位置查、非整串 sniff**。 与…** (1 connections) — `core/gherkai_core/adapters/run_store/arg_offload.py`
- *... and 8 more nodes in this community*

## Relationships

- [Job Domain Models](Job_Domain_Models.md) (9 shared connections)
- [Cloud Store Adapters](Cloud_Store_Adapters.md) (7 shared connections)
- [Run Result Aggregation Tree](Run_Result_Aggregation_Tree.md) (6 shared connections)
- [S3 Store Adapters](S3_Store_Adapters.md) (5 shared connections)
- [Event Log Adapters](Event_Log_Adapters.md) (2 shared connections)
- [Atomic Write and Report Stores](Atomic_Write_and_Report_Stores.md) (2 shared connections)
- [Cloud Integration Tests](Cloud_Integration_Tests.md) (2 shared connections)
- [Run State Store](Run_State_Store.md) (2 shared connections)
- [Cloud Reconcile Tests](Cloud_Reconcile_Tests.md) (1 shared connections)
- [Fargate Engine Adapter](Fargate_Engine_Adapter.md) (1 shared connections)
- [ECS Timeout Handling Tests](ECS_Timeout_Handling_Tests.md) (1 shared connections)
- [SSM Path Naming](SSM_Path_Naming.md) (1 shared connections)

## Source Files

- `core/gherkai_core/adapters/_boto.py`
- `core/gherkai_core/adapters/report_store/s3.py`
- `core/gherkai_core/adapters/result_store/s3.py`
- `core/gherkai_core/adapters/run_store/arg_offload.py`
- `core/gherkai_core/adapters/run_store/ddb.py`
- `core/tests/conftest.py`

## Audit Trail

- EXTRACTED: 67 (84%)
- INFERRED: 13 (16%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*