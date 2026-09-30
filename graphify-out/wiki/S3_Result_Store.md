# S3 Result Store

> 25 nodes · cohesion 0.12

## Key Concepts

- **S3ResultStore** (17 connections) — `core/gherkai_core/adapters/result_store/s3.py`
- **test_s3_result_store.py** (15 connections) — `core/tests/test_s3_result_store.py`
- **_job_def()** (14 connections) — `core/tests/test_stores.py`
- **test_job_timeout_s_round_trip()** (6 connections) — `core/tests/test_stores.py`
- **.load_all()** (5 connections) — `core/gherkai_core/adapters/result_store/s3.py`
- **.load_job_result()** (5 connections) — `core/gherkai_core/adapters/result_store/s3.py`
- **.save_job_result()** (5 connections) — `core/gherkai_core/adapters/result_store/s3.py`
- **test_result_store_scope_id_not_path_traversal()** (5 connections) — `core/tests/test_stores.py`
- **._key()** (4 connections) — `core/gherkai_core/adapters/result_store/s3.py`
- **test_prefix_isolates_runs()** (4 connections) — `core/tests/test_s3_result_store.py`
- **._jobs_prefix()** (3 connections) — `core/gherkai_core/adapters/result_store/s3.py`
- **test_load_all_paginated_preserves_failed_verdict()** (3 connections) — `core/tests/test_s3_result_store.py`
- **test_load_all_paginates_beyond_1000()** (3 connections) — `core/tests/test_s3_result_store.py`
- **test_load_all_stable_order()** (3 connections) — `core/tests/test_s3_result_store.py`
- **test_scope_id_with_slash_not_subprefix()** (3 connections) — `core/tests/test_s3_result_store.py`
- **.preflight()** (2 connections) — `core/gherkai_core/adapters/result_store/s3.py`
- **test_save_load_round_trip()** (2 connections) — `core/tests/test_s3_result_store.py`
- **Job** (2 connections)
- **ResultStore 的 S3 实装（组合根注入 boto3 s3 client + bucket + 可选 key 前缀）。行为对拍…** (1 connections) — `core/gherkai_core/adapters/result_store/s3.py`
- **把单个 JobResult 存成一个 S3 对象（写面，追加语义即同 key 覆盖，幂等）。** (1 connections) — `core/gherkai_core/adapters/result_store/s3.py`
- **读回单个 JobResult（按键取，无需查询）；不存在返回 None。** (1 connections) — `core/gherkai_core/adapters/result_store/s3.py`
- **读回某 run 的全部 JobResult（CI 遍历用）。无则空 list。 **必须翻页**：list_objects_v2 单页硬上限 1000…** (1 connections) — `core/gherkai_core/adapters/result_store/s3.py`
- **探活（ADR 0030 决定七）：begin 前探桶可达，桶不存在/无权限即抛（cli 接住→以退出码 2 结束）。** (1 connections) — `core/gherkai_core/adapters/result_store/s3.py`
- **S3ResultStore 对拍测试（ADR 0030 决定六 / 0016）：与 LocalResultStore 同一批行为断言，moto…** (1 connections) — `core/tests/test_s3_result_store.py`
- **test_load_missing_returns_none()** (1 connections) — `core/tests/test_s3_result_store.py`

## Relationships

- [Result Tree Text Rendering](Result_Tree_Text_Rendering.md) (12 shared connections)
- [Run State Rendering](Run_State_Rendering.md) (8 shared connections)
- [Result Store Serialization](Result_Store_Serialization.md) (6 shared connections)
- [Run Definition Domain Model](Run_Definition_Domain_Model.md) (4 shared connections)
- [DynamoDB Run Store](DynamoDB_Run_Store.md) (2 shared connections)
- [S3 Step Argument Offload](S3_Step_Argument_Offload.md) (2 shared connections)
- [CLI Test Fixtures](CLI_Test_Fixtures.md) (1 shared connections)
- [Boto3 Adapter Guard](Boto3_Adapter_Guard.md) (1 shared connections)
- [Core Adapters Documentation](Core_Adapters_Documentation.md) (1 shared connections)
- [Run Persistence Orchestration](Run_Persistence_Orchestration.md) (1 shared connections)

## Source Files

- `core/gherkai_core/adapters/result_store/s3.py`
- `core/tests/test_s3_result_store.py`
- `core/tests/test_stores.py`

## Audit Trail

- EXTRACTED: 71 (97%)
- INFERRED: 2 (3%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*