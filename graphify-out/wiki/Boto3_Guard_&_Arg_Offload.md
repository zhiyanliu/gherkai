# Boto3 Guard & Arg Offload

> 27 nodes · cohesion 0.08

## Key Concepts

- **require_boto3()** (14 connections) — `core/gherkai_core/adapters/_boto.py`
- **event_log/ddb.py** (12 connections) — `core/gherkai_core/adapters/event_log/ddb.py`
- **_boto.py** (8 connections) — `core/gherkai_core/adapters/_boto.py`
- **arg_offload.py** (7 connections) — `core/gherkai_core/adapters/run_store/arg_offload.py`
- **has_pointers()** (5 connections) — `core/gherkai_core/adapters/run_store/arg_offload.py`
- **_iter_arguments()** (5 connections) — `core/gherkai_core/adapters/run_store/arg_offload.py`
- **.load_run_meta()** (5 connections) — `core/gherkai_core/adapters/run_store/ddb.py`
- **.restore()** (4 connections) — `core/gherkai_core/adapters/run_store/arg_offload.py`
- **.__init__()** (3 connections) — `core/gherkai_core/adapters/report_store/s3.py`
- **.__init__()** (3 connections) — `core/gherkai_core/adapters/result_store/s3.py`
- **._fetch()** (3 connections) — `core/gherkai_core/adapters/run_store/arg_offload.py`
- **.__init__()** (3 connections) — `core/gherkai_core/adapters/run_store/arg_offload.py`
- **.__init__()** (3 connections) — `core/gherkai_core/adapters/run_store/ddb.py`
- **.__init__()** (2 connections) — `core/gherkai_core/adapters/fargate_engine.py`
- **云端 adapter 共享的 boto3 依赖守卫（ADR 0016 窄腰 / 0030 决定六方案 A）。 凡走 `aws` extra 的 adapter…** (1 connections) — `core/gherkai_core/adapters/_boto.py`
- **缺 boto3 时抛带组件名的友好 ImportError（`pip install 'gherkai-core[aws]'`）；模块 import…** (1 connections) — `core/gherkai_core/adapters/_boto.py`
- **DdbEventLog（ADR 0034 cloud 侧）：cloud 无状态批量运行的 EventLog——从 DDB events 表读全量重放 + 写…** (1 connections) — `core/gherkai_core/adapters/event_log/ddb.py`
- **s3_client：boto3 s3 client（组合根注入；建桶责任在 IaC，adapter 假定桶已存在）。 prefix：可选 key 前缀（如…** (1 connections) — `core/gherkai_core/adapters/report_store/s3.py`
- **s3_client：boto3 s3 client（组合根注入；建桶责任在 IaC，adapter 假定桶已存在）。 prefix：可选 key 前缀（如…** (1 connections) — `core/gherkai_core/adapters/result_store/s3.py`
- **StepArgument S3 offload（ADR 0030 决定六）：把 RunMeta 深树里的 docString/dataTable 换成 S3…** (1 connections) — `core/gherkai_core/adapters/run_store/arg_offload.py`
- **按 s3:// URI 取回 JSON 值（解析出 bucket/key，不重算——URI 自描述）。** (1 connections) — `core/gherkai_core/adapters/run_store/arg_offload.py`
- **遍历 run_meta_to_dict 产物里每个带 argument 的 step，yield (arg_dict, scope_id,…** (1 connections) — `core/gherkai_core/adapters/run_store/arg_offload.py`
- **meta_dict 里是否存在 offload 指针（`content_ref`/`rows_ref`）——**按位置查、非整串 sniff**。 与…** (1 connections) — `core/gherkai_core/adapters/run_store/arg_offload.py`
- **s3_client：boto3 s3 client（组合根注入；建桶责任在 IaC）。prefix：可选 key 前缀。** (1 connections) — `core/gherkai_core/adapters/run_store/arg_offload.py`
- **就地把 content_ref / rows_ref 取回、消解回内联 content / rows（offload 的逆）。 按「哪个 _ref…** (1 connections) — `core/gherkai_core/adapters/run_store/arg_offload.py`
- *... and 2 more nodes in this community*

## Relationships

- [Cloud Launcher & Fargate Adapters](Cloud_Launcher_%26_Fargate_Adapters.md) (11 shared connections)
- [Job/Scenario Explain Model](Job-Scenario_Explain_Model.md) (8 shared connections)
- [S3 Result Store](S3_Result_Store.md) (3 shared connections)
- [DynamoDB Event Log](DynamoDB_Event_Log.md) (3 shared connections)
- [Report Store Collection](Report_Store_Collection.md) (2 shared connections)
- [Fake DDB Table & SQLite Records](Fake_DDB_Table_%26_SQLite_Records.md) (2 shared connections)
- [SQLite Event Log Adapter](SQLite_Event_Log_Adapter.md) (1 shared connections)
- [Wire Protocol Serialization](Wire_Protocol_Serialization.md) (1 shared connections)
- [Job State Serialization](Job_State_Serialization.md) (1 shared connections)

## Source Files

- `core/gherkai_core/adapters/_boto.py`
- `core/gherkai_core/adapters/event_log/ddb.py`
- `core/gherkai_core/adapters/fargate_engine.py`
- `core/gherkai_core/adapters/report_store/s3.py`
- `core/gherkai_core/adapters/result_store/s3.py`
- `core/gherkai_core/adapters/run_store/arg_offload.py`
- `core/gherkai_core/adapters/run_store/ddb.py`

## Audit Trail

- EXTRACTED: 61 (100%)
- INFERRED: 0 (0%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*