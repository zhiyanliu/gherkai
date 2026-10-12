# S3 Result Store

> 31 nodes · cohesion 0.11

## Key Concepts

- **JobResult** (84 connections) — `core/gherkai_core/model.py`
- **S3ResultStore** (17 connections) — `core/gherkai_core/adapters/result_store/s3.py`
- **test_s3_result_store.py** (15 connections) — `core/tests/test_s3_result_store.py`
- **_job_def()** (14 connections) — `core/tests/test_stores.py`
- **test_job_timeout_s_round_trip()** (6 connections) — `core/tests/test_stores.py`
- **.load_all()** (5 connections) — `core/gherkai_core/adapters/result_store/s3.py`
- **.load_job_result()** (5 connections) — `core/gherkai_core/adapters/result_store/s3.py`
- **.save_job_result()** (5 connections) — `core/gherkai_core/adapters/result_store/s3.py`
- **.on_job_complete()** (5 connections) — `core/gherkai_core/persist.py`
- **test_result_store_scope_id_not_path_traversal()** (5 connections) — `core/tests/test_stores.py`
- **._key()** (4 connections) — `core/gherkai_core/adapters/result_store/s3.py`
- **test_prefix_isolates_runs()** (4 connections) — `core/tests/test_s3_result_store.py`
- **._jobs_prefix()** (3 connections) — `core/gherkai_core/adapters/result_store/s3.py`
- **test_load_all_paginated_preserves_failed_verdict()** (3 connections) — `core/tests/test_s3_result_store.py`
- **test_load_all_paginates_beyond_1000()** (3 connections) — `core/tests/test_s3_result_store.py`
- **test_load_all_stable_order()** (3 connections) — `core/tests/test_s3_result_store.py`
- **test_scope_id_with_slash_not_subprefix()** (3 connections) — `core/tests/test_s3_result_store.py`
- **.preflight()** (2 connections) — `core/gherkai_core/adapters/result_store/s3.py`
- **.scope_id()** (2 connections) — `core/gherkai_core/model.py`
- **test_save_load_round_trip()** (2 connections) — `core/tests/test_s3_result_store.py`
- **Job** (2 connections)
- **ResultStore 的 S3 实装（组合根注入 boto3 s3 client + bucket + 可选 key 前缀）。行为对拍…** (1 connections) — `core/gherkai_core/adapters/result_store/s3.py`
- **把单个 JobResult 存成一个 S3 对象（写面，追加语义即同 key 覆盖，幂等）。** (1 connections) — `core/gherkai_core/adapters/result_store/s3.py`
- **读回单个 JobResult（按键取，无需查询）；不存在返回 None。** (1 connections) — `core/gherkai_core/adapters/result_store/s3.py`
- **读回某 run 的全部 JobResult（CI 遍历用）。无则空 list。 **必须翻页**：list_objects_v2 单页硬上限 1000…** (1 connections) — `core/gherkai_core/adapters/result_store/s3.py`
- *... and 6 more nodes in this community*

## Relationships

- [Cloud Adapter Boundary Modules](Cloud_Adapter_Boundary_Modules.md) (21 shared connections)
- [Result Store Adapters](Result_Store_Adapters.md) (14 shared connections)
- [DynamoDB Job State Store](DynamoDB_Job_State_Store.md) (11 shared connections)
- [Result Tree Rendering](Result_Tree_Rendering.md) (8 shared connections)
- [Run Persistence Local Stores](Run_Persistence_Local_Stores.md) (8 shared connections)
- [Job Explain Data Model](Job_Explain_Data_Model.md) (7 shared connections)
- [Explain Reads And Report Store](Explain_Reads_And_Report_Store.md) (5 shared connections)
- [Store Port Definitions](Store_Port_Definitions.md) (5 shared connections)
- [Run Scheduling Events Core](Run_Scheduling_Events_Core.md) (3 shared connections)
- [Cloud Adapter Test Fixtures](Cloud_Adapter_Test_Fixtures.md) (2 shared connections)
- [Terminal State Aggregation](Terminal_State_Aggregation.md) (2 shared connections)
- [Step Argument S3 Offload](Step_Argument_S3_Offload.md) (2 shared connections)

## Source Files

- `core/gherkai_core/adapters/result_store/s3.py`
- `core/gherkai_core/model.py`
- `core/gherkai_core/persist.py`
- `core/tests/test_s3_result_store.py`
- `core/tests/test_stores.py`

## Audit Trail

- EXTRACTED: 125 (83%)
- INFERRED: 26 (17%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*