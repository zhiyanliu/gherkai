# AWS Adapter Clients

> 12 nodes · cohesion 0.17

## Key Concepts

- **require_boto3()** (14 connections) — `core/gherkai_core/adapters/_boto.py`
- **.__init__()** (3 connections) — `core/gherkai_core/adapters/report_store/s3.py`
- **.__init__()** (3 connections) — `core/gherkai_core/adapters/result_store/s3.py`
- **.__init__()** (3 connections) — `core/gherkai_core/adapters/run_store/arg_offload.py`
- **.__init__()** (3 connections) — `core/gherkai_core/adapters/run_store/ddb.py`
- **.__init__()** (2 connections) — `core/gherkai_core/adapters/event_log/ddb.py`
- **.__init__()** (2 connections) — `core/gherkai_core/adapters/fargate_engine.py`
- **缺 boto3 时抛带组件名的友好 ImportError（`pip install 'gherkai-core[aws]'`）；模块 import…** (1 connections) — `core/gherkai_core/adapters/_boto.py`
- **s3_client：boto3 s3 client（组合根注入；建桶责任在 IaC，adapter 假定桶已存在）。 prefix：可选 key 前缀（如…** (1 connections) — `core/gherkai_core/adapters/report_store/s3.py`
- **s3_client：boto3 s3 client（组合根注入；建桶责任在 IaC，adapter 假定桶已存在）。 prefix：可选 key 前缀（如…** (1 connections) — `core/gherkai_core/adapters/result_store/s3.py`
- **s3_client：boto3 s3 client（组合根注入；建桶责任在 IaC）。prefix：可选 key 前缀。** (1 connections) — `core/gherkai_core/adapters/run_store/arg_offload.py`
- **table：boto3 dynamodb.Table 资源（组合根注入；建表责任在 IaC，adapter 假定已存在）。 arg_offloader：可选…** (1 connections) — `core/gherkai_core/adapters/run_store/ddb.py`

## Relationships

- [DynamoDB Event Log](DynamoDB_Event_Log.md) (3 shared connections)
- [Boto Guard & Arg Offload](Boto_Guard_%26_Arg_Offload.md) (2 shared connections)
- [Run Metadata & S3 Offload](Run_Metadata_%26_S3_Offload.md) (2 shared connections)
- [Report Store Adapters](Report_Store_Adapters.md) (1 shared connections)
- [Local & S3 Result Stores](Local_%26_S3_Result_Stores.md) (1 shared connections)
- [Run State Rendering](Run_State_Rendering.md) (1 shared connections)
- [Fargate Engine Adapter](Fargate_Engine_Adapter.md) (1 shared connections)
- [S3 Report Store](S3_Report_Store.md) (1 shared connections)
- [S3 Result Store Port](S3_Result_Store_Port.md) (1 shared connections)

## Source Files

- `core/gherkai_core/adapters/_boto.py`
- `core/gherkai_core/adapters/event_log/ddb.py`
- `core/gherkai_core/adapters/fargate_engine.py`
- `core/gherkai_core/adapters/report_store/s3.py`
- `core/gherkai_core/adapters/result_store/s3.py`
- `core/gherkai_core/adapters/run_store/arg_offload.py`
- `core/gherkai_core/adapters/run_store/ddb.py`

## Audit Trail

- EXTRACTED: 24 (100%)
- INFERRED: 0 (0%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*