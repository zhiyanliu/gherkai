# Boto Guard & Arg Offload

> 17 nodes · cohesion 0.12

## Key Concepts

- **_boto.py** (8 connections) — `core/gherkai_core/adapters/_boto.py`
- **arg_offload.py** (7 connections) — `core/gherkai_core/adapters/run_store/arg_offload.py`
- **has_pointers()** (5 connections) — `core/gherkai_core/adapters/run_store/arg_offload.py`
- **_iter_arguments()** (5 connections) — `core/gherkai_core/adapters/run_store/arg_offload.py`
- **.offload()** (5 connections) — `core/gherkai_core/adapters/run_store/arg_offload.py`
- **.restore()** (4 connections) — `core/gherkai_core/adapters/run_store/arg_offload.py`
- **._fetch()** (3 connections) — `core/gherkai_core/adapters/run_store/arg_offload.py`
- **._put()** (3 connections) — `core/gherkai_core/adapters/run_store/arg_offload.py`
- **._key()** (2 connections) — `core/gherkai_core/adapters/run_store/arg_offload.py`
- **云端 adapter 共享的 boto3 依赖守卫（ADR 0016 窄腰 / 0030 决定六方案 A）。 凡走 `aws` extra 的 adapter…** (1 connections) — `core/gherkai_core/adapters/_boto.py`
- **StepArgument S3 offload（ADR 0030 决定六）：把 RunMeta 深树里的 docString/dataTable 换成 S3…** (1 connections) — `core/gherkai_core/adapters/run_store/arg_offload.py`
- **按 s3:// URI 取回 JSON 值（解析出 bucket/key，不重算——URI 自描述）。** (1 connections) — `core/gherkai_core/adapters/run_store/arg_offload.py`
- **遍历 run_meta_to_dict 产物里每个带 argument 的 step，yield (arg_dict, scope_id,…** (1 connections) — `core/gherkai_core/adapters/run_store/arg_offload.py`
- **meta_dict 里是否存在 offload 指针（`content_ref`/`rows_ref`）——**按位置查、非整串 sniff**。 与…** (1 connections) — `core/gherkai_core/adapters/run_store/arg_offload.py`
- **把值 JSON 化上传，返回 s3:// URI（自描述指针，restore 直接按它取回、不重算 key）。** (1 connections) — `core/gherkai_core/adapters/run_store/arg_offload.py`
- **就地把每个 docString 的 content / dataTable 的 rows 搬 S3、原键换成 content_ref / rows_ref。…** (1 connections) — `core/gherkai_core/adapters/run_store/arg_offload.py`
- **就地把 content_ref / rows_ref 取回、消解回内联 content / rows（offload 的逆）。 按「哪个 _ref…** (1 connections) — `core/gherkai_core/adapters/run_store/arg_offload.py`

## Relationships

- [Run Metadata & S3 Offload](Run_Metadata_%26_S3_Offload.md) (7 shared connections)
- [Run State Rendering](Run_State_Rendering.md) (3 shared connections)
- [DynamoDB Event Log](DynamoDB_Event_Log.md) (2 shared connections)
- [AWS Adapter Clients](AWS_Adapter_Clients.md) (2 shared connections)
- [Report Store Adapters](Report_Store_Adapters.md) (1 shared connections)
- [Local & S3 Result Stores](Local_%26_S3_Result_Stores.md) (1 shared connections)

## Source Files

- `core/gherkai_core/adapters/_boto.py`
- `core/gherkai_core/adapters/run_store/arg_offload.py`

## Audit Trail

- EXTRACTED: 33 (100%)
- INFERRED: 0 (0%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*