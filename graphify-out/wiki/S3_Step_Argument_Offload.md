# S3 Step Argument Offload

> 29 nodes · cohesion 0.09

## Key Concepts

- **S3StepArgumentOffloader** (20 connections) — `core/gherkai_core/adapters/run_store/arg_offload.py`
- **core/tests/conftest.py** (14 connections) — `core/tests/conftest.py`
- **build_cloud_stores()** (11 connections) — `runtime/gherkai_runtime/compose.py`
- **arg_offload.py** (7 connections) — `core/gherkai_core/adapters/run_store/arg_offload.py`
- **has_pointers()** (5 connections) — `core/gherkai_core/adapters/run_store/arg_offload.py`
- **_iter_arguments()** (5 connections) — `core/gherkai_core/adapters/run_store/arg_offload.py`
- **.offload()** (5 connections) — `core/gherkai_core/adapters/run_store/arg_offload.py`
- **.load_run_meta()** (5 connections) — `core/gherkai_core/adapters/run_store/ddb.py`
- **.restore()** (4 connections) — `core/gherkai_core/adapters/run_store/arg_offload.py`
- **arg_offloader()** (4 connections) — `core/tests/conftest.py`
- **ddb_run_store()** (4 connections) — `core/tests/conftest.py`
- **ddb_run_store_offload()** (4 connections) — `core/tests/conftest.py`
- **._fetch()** (3 connections) — `core/gherkai_core/adapters/run_store/arg_offload.py`
- **._put()** (3 connections) — `core/gherkai_core/adapters/run_store/arg_offload.py`
- **._key()** (2 connections) — `core/gherkai_core/adapters/run_store/arg_offload.py`
- **StepArgument S3 offload（ADR 0030 决定六）：把 RunMeta 深树里的 docString/dataTable 换成 S3…** (1 connections) — `core/gherkai_core/adapters/run_store/arg_offload.py`
- **按 s3:// URI 取回 JSON 值（解析出 bucket/key，不重算——URI 自描述）。** (1 connections) — `core/gherkai_core/adapters/run_store/arg_offload.py`
- **遍历 run_meta_to_dict 产物里每个带 argument 的 step，yield (arg_dict, scope_id,…** (1 connections) — `core/gherkai_core/adapters/run_store/arg_offload.py`
- **meta_dict 里是否存在 offload 指针（`content_ref`/`rows_ref`）——**按位置查、非整串 sniff**。 与…** (1 connections) — `core/gherkai_core/adapters/run_store/arg_offload.py`
- **把 RunMeta 里 docString/dataTable 的正文搬 S3（DynamoDBRunStore 注入）。offload/restore…** (1 connections) — `core/gherkai_core/adapters/run_store/arg_offload.py`
- **把值 JSON 化上传，返回 s3:// URI（自描述指针，restore 直接按它取回、不重算 key）。** (1 connections) — `core/gherkai_core/adapters/run_store/arg_offload.py`
- **就地把每个 docString 的 content / dataTable 的 rows 搬 S3、原键换成 content_ref / rows_ref。…** (1 connections) — `core/gherkai_core/adapters/run_store/arg_offload.py`
- **就地把 content_ref / rows_ref 取回、消解回内联 content / rows（offload 的逆）。 按「哪个 _ref…** (1 connections) — `core/gherkai_core/adapters/run_store/arg_offload.py`
- **读回 definition（从 META item 的 meta_json）；不存在返回 None。** (1 connections) — `core/gherkai_core/adapters/run_store/ddb.py`
- **云端 adapter 测试基建（ADR 0030 决定六）。 **两类测试、两套 fixture**（见 tests/README.md）： -…** (1 connections) — `core/tests/conftest.py`
- *... and 4 more nodes in this community*

## Relationships

- [CLI Test Fixtures](CLI_Test_Fixtures.md) (9 shared connections)
- [DynamoDB Run Store](DynamoDB_Run_Store.md) (7 shared connections)
- [Run Definition Domain Model](Run_Definition_Domain_Model.md) (6 shared connections)
- [Boto3 Adapter Guard](Boto3_Adapter_Guard.md) (3 shared connections)
- [Run State Rendering](Run_State_Rendering.md) (3 shared connections)
- [Cloud Engine Resolver Build](Cloud_Engine_Resolver_Build.md) (3 shared connections)
- [Lambda Handler Event Tests](Lambda_Handler_Event_Tests.md) (2 shared connections)
- [Report Store Adapters](Report_Store_Adapters.md) (2 shared connections)
- [S3 Result Store](S3_Result_Store.md) (2 shared connections)
- [Composition Root Helpers](Composition_Root_Helpers.md) (2 shared connections)
- [Cloud Composition Helpers](Cloud_Composition_Helpers.md) (1 shared connections)

## Source Files

- `core/gherkai_core/adapters/run_store/arg_offload.py`
- `core/gherkai_core/adapters/run_store/ddb.py`
- `core/tests/conftest.py`
- `runtime/gherkai_runtime/compose.py`

## Audit Trail

- EXTRACTED: 66 (88%)
- INFERRED: 9 (12%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*