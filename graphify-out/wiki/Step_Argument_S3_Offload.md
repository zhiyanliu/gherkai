# Step Argument S3 Offload

> 37 nodes · cohesion 0.06

## Key Concepts

- **S3StepArgumentOffloader** (27 connections) — `core/gherkai_core/adapters/run_store/arg_offload.py`
- **WorkerVariantError** (26 connections) — `runtime/gherkai_runtime/compose.py`
- **Engine** (22 connections) — `core/gherkai_core/ports.py`
- **_FakeSchedulerClient** (17 connections) — `deploy_aws/tests/test_lambda_handlers.py`
- **WorkerHandle** (12 connections) — `core/gherkai_core/ports.py`
- **arg_offload.py** (7 connections) — `core/gherkai_core/adapters/run_store/arg_offload.py`
- **has_pointers()** (5 connections) — `core/gherkai_core/adapters/run_store/arg_offload.py`
- **_iter_arguments()** (5 connections) — `core/gherkai_core/adapters/run_store/arg_offload.py`
- **.offload()** (5 connections) — `core/gherkai_core/adapters/run_store/arg_offload.py`
- **.run_scope()** (5 connections) — `core/gherkai_core/ports.py`
- **.restore()** (4 connections) — `core/gherkai_core/adapters/run_store/arg_offload.py`
- **._fetch()** (3 connections) — `core/gherkai_core/adapters/run_store/arg_offload.py`
- **._put()** (3 connections) — `core/gherkai_core/adapters/run_store/arg_offload.py`
- **test_timeout_watch_conflict_is_idempotent()** (3 connections) — `deploy_aws/tests/test_lambda_handlers.py`
- **._key()** (2 connections) — `core/gherkai_core/adapters/run_store/arg_offload.py`
- **Event** (2 connections)
- **.__call__()** (2 connections) — `core/gherkai_core/ports.py`
- **.stop()** (2 connections) — `core/gherkai_core/ports.py`
- **test_timeout_watch_creates_one_time_schedule()** (2 connections) — `deploy_aws/tests/test_lambda_handlers.py`
- **StepArgument S3 offload（ADR 0030 决定六）：把 RunMeta 深树里的 docString/dataTable 换成 S3…** (1 connections) — `core/gherkai_core/adapters/run_store/arg_offload.py`
- **按 s3:// URI 取回 JSON 值（解析出 bucket/key，不重算——URI 自描述）。** (1 connections) — `core/gherkai_core/adapters/run_store/arg_offload.py`
- **遍历 run_meta_to_dict 产物里每个带 argument 的 step，yield (arg_dict, scope_id,…** (1 connections) — `core/gherkai_core/adapters/run_store/arg_offload.py`
- **meta_dict 里是否存在 offload 指针（`content_ref`/`rows_ref`）——**按位置查、非整串 sniff**。 与…** (1 connections) — `core/gherkai_core/adapters/run_store/arg_offload.py`
- **把 RunMeta 里 docString/dataTable 的正文搬 S3（DynamoDBRunStore 注入）。offload/restore…** (1 connections) — `core/gherkai_core/adapters/run_store/arg_offload.py`
- **把值 JSON 化上传，返回 s3:// URI（自描述指针，restore 直接按它取回、不重算 key）。** (1 connections) — `core/gherkai_core/adapters/run_store/arg_offload.py`
- *... and 12 more nodes in this community*

## Relationships

- [Job Explain Data Model](Job_Explain_Data_Model.md) (20 shared connections)
- [Store Port Definitions](Store_Port_Definitions.md) (14 shared connections)
- [Cloud Adapter Boundary Modules](Cloud_Adapter_Boundary_Modules.md) (10 shared connections)
- [SSM Paths And Compose](SSM_Paths_And_Compose.md) (7 shared connections)
- [DynamoDB Job State Store](DynamoDB_Job_State_Store.md) (5 shared connections)
- [Lambda Handler Event Parsing Tests](Lambda_Handler_Event_Parsing_Tests.md) (5 shared connections)
- [Run State Store](Run_State_Store.md) (4 shared connections)
- [boto3 Client Injection](boto3_Client_Injection.md) (2 shared connections)
- [Cloud Adapter Test Fixtures](Cloud_Adapter_Test_Fixtures.md) (2 shared connections)
- [Cloud Compose Root](Cloud_Compose_Root.md) (2 shared connections)
- [Local Compose Root](Local_Compose_Root.md) (2 shared connections)
- [S3 Result Store](S3_Result_Store.md) (2 shared connections)

## Source Files

- `core/gherkai_core/adapters/run_store/arg_offload.py`
- `core/gherkai_core/ports.py`
- `deploy_aws/tests/test_lambda_handlers.py`
- `runtime/gherkai_runtime/compose.py`

## Audit Trail

- EXTRACTED: 71 (55%)
- INFERRED: 58 (45%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*