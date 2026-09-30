# Boto3 Adapter Guard

> 17 nodes · cohesion 0.13

## Key Concepts

- **require_boto3()** (14 connections) — `core/gherkai_core/adapters/_boto.py`
- **event_log/ddb.py** (12 connections) — `core/gherkai_core/adapters/event_log/ddb.py`
- **report_store/s3.py** (9 connections) — `core/gherkai_core/adapters/report_store/s3.py`
- **_boto.py** (8 connections) — `core/gherkai_core/adapters/_boto.py`
- **.__init__()** (3 connections) — `core/gherkai_core/adapters/report_store/s3.py`
- **.__init__()** (3 connections) — `core/gherkai_core/adapters/result_store/s3.py`
- **.__init__()** (3 connections) — `core/gherkai_core/adapters/run_store/arg_offload.py`
- **.__init__()** (3 connections) — `core/gherkai_core/adapters/run_store/ddb.py`
- **.__init__()** (2 connections) — `core/gherkai_core/adapters/event_log/ddb.py`
- **云端 adapter 共享的 boto3 依赖守卫（ADR 0016 窄腰 / 0030 决定六方案 A）。 凡走 `aws` extra 的 adapter…** (1 connections) — `core/gherkai_core/adapters/_boto.py`
- **缺 boto3 时抛带组件名的友好 ImportError（`pip install 'gherkai-core[aws]'`）；模块 import…** (1 connections) — `core/gherkai_core/adapters/_boto.py`
- **DdbEventLog（ADR 0034 cloud 侧）：cloud 无状态批量运行的 EventLog——从 DDB events 表读全量重放 + 写…** (1 connections) — `core/gherkai_core/adapters/event_log/ddb.py`
- **S3ReportStore（ADR 0030 决定六 / 0027 / 0029）：ReportStore port 的 S3 实装。 把一次 run 的…** (1 connections) — `core/gherkai_core/adapters/report_store/s3.py`
- **s3_client：boto3 s3 client（组合根注入；建桶责任在 IaC，adapter 假定桶已存在）。 prefix：可选 key 前缀（如…** (1 connections) — `core/gherkai_core/adapters/report_store/s3.py`
- **s3_client：boto3 s3 client（组合根注入；建桶责任在 IaC，adapter 假定桶已存在）。 prefix：可选 key 前缀（如…** (1 connections) — `core/gherkai_core/adapters/result_store/s3.py`
- **s3_client：boto3 s3 client（组合根注入；建桶责任在 IaC）。prefix：可选 key 前缀。** (1 connections) — `core/gherkai_core/adapters/run_store/arg_offload.py`
- **table：boto3 dynamodb.Table 资源（组合根注入；建表责任在 IaC，adapter 假定已存在）。 arg_offloader：可选…** (1 connections) — `core/gherkai_core/adapters/run_store/ddb.py`

## Relationships

- [Core Adapters Documentation](Core_Adapters_Documentation.md) (4 shared connections)
- [S3 Step Argument Offload](S3_Step_Argument_Offload.md) (3 shared connections)
- [Atomic Local Writes](Atomic_Local_Writes.md) (3 shared connections)
- [Result Store Serialization](Result_Store_Serialization.md) (2 shared connections)
- [Run State Rendering](Run_State_Rendering.md) (2 shared connections)
- [Event Records Projection](Event_Records_Projection.md) (2 shared connections)
- [Event Wire Serialization](Event_Wire_Serialization.md) (2 shared connections)
- [Result Tree Text Rendering](Result_Tree_Text_Rendering.md) (2 shared connections)
- [Cloud Launcher and EventLog](Cloud_Launcher_and_EventLog.md) (2 shared connections)
- [Report Store Adapters](Report_Store_Adapters.md) (2 shared connections)
- [Fargate Engine Adapter](Fargate_Engine_Adapter.md) (1 shared connections)
- [SQLite Event Log](SQLite_Event_Log.md) (1 shared connections)

## Source Files

- `core/gherkai_core/adapters/_boto.py`
- `core/gherkai_core/adapters/event_log/ddb.py`
- `core/gherkai_core/adapters/report_store/s3.py`
- `core/gherkai_core/adapters/result_store/s3.py`
- `core/gherkai_core/adapters/run_store/arg_offload.py`
- `core/gherkai_core/adapters/run_store/ddb.py`

## Audit Trail

- EXTRACTED: 47 (100%)
- INFERRED: 0 (0%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*