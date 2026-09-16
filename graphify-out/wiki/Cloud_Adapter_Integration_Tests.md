# Cloud Adapter Integration Tests

> 25 nodes · cohesion 0.15

## Key Concepts

- **test_cloud_integration.py** (28 connections) — `core/tests/test_cloud_integration.py`
- **test_offload_unblocks_oversized_docstring_real()** (12 connections) — `core/tests/test_cloud_integration.py`
- **test_offload_round_trip_real()** (11 connections) — `core/tests/test_cloud_integration.py`
- **_uniq()** (10 connections) — `core/tests/test_cloud_integration.py`
- **_ddb_store()** (9 connections) — `core/tests/test_cloud_integration.py`
- **test_ddb_state_item_grows_past_400kb_on_incremental_update_real()** (8 connections) — `core/tests/test_cloud_integration.py`
- **test_ddb_empty_string_scalar_and_map_entry_real()** (7 connections) — `core/tests/test_cloud_integration.py`
- **test_ddb_run_store_lifecycle_real()** (7 connections) — `core/tests/test_cloud_integration.py`
- **test_ddb_session_id_none_omitted_real()** (7 connections) — `core/tests/test_cloud_integration.py`
- **test_ddb_update_before_create_raises_real()** (5 connections) — `core/tests/test_cloud_integration.py`
- **test_s3_result_store_round_trip_real()** (5 connections) — `core/tests/test_cloud_integration.py`
- **_is_ddb_too_large()** (4 connections) — `core/tests/test_cloud_integration.py`
- **_offloader()** (4 connections) — `core/tests/test_cloud_integration.py`
- **_s3_result_store()** (3 connections) — `core/tests/test_cloud_integration.py`
- **云端 adapter 集成测试（@pytest.mark.integration）：连**真** DDB/S3，专测 moto 抓不到的真 AWS 语义。…** (1 connections) — `core/tests/test_cloud_integration.py`
- **真 S3：save/load/load_all round-trip，含 /:中文 scope_id 的 quote 编码在真 S3 不撞名/不造子前缀。** (1 connections) — `core/tests/test_cloud_integration.py`
- **真 S3：DynamoDBRunStore 挂 offloader，docString/dataTable 搬真 S3、META 只留指针、读回逐字节还原。** (1 connections) — `core/tests/test_cloud_integration.py`
- **真 DDB item 超 400KB 的 ValidationException 判定（不硬编字节数/次数，躲阈值/版本漂移的 flaky）。** (1 connections) — `core/tests/test_cloud_integration.py`
- **真 DDB：STATE item 经反复 `SET jobs.#sid` 增量长大、整个 item 越过 400KB 时 update_item 抛…** (1 connections) — `core/tests/test_cloud_integration.py`
- **真 DDB+S3 因果闭环：含 >400KB docString 的 RunMeta——不挂 offloader 时 create_run 撞 400KB…** (1 connections) — `core/tests/test_cloud_integration.py`
- **真 DDB（2026）空串行为的回归基线：finalize 写 ended_at=""（顶层标量 SET）、update 写 session_id=""…** (1 connections) — `core/tests/test_cloud_integration.py`
- **给真表/真桶造一个本次运行专属的 run_id，避免多次跑撞名（无随机源，用递增计数）。 跨进程靠 it- 前缀 + fixture…** (1 connections) — `core/tests/test_cloud_integration.py`
- **真 DDB 上跑完整实时写生命周期：create_run → update_job_state（RUNNING→终态）→ finalize_run → 读回。…** (1 connections) — `core/tests/test_cloud_integration.py`
- **真 DDB：未 create 就 update/finalize → ConditionalCheckFailedException 转…** (1 connections) — `core/tests/test_cloud_integration.py`
- **真 DDB：session_id=None omit-when-None，读回仍 None（真 Map entry 缺键的读回语义）。** (1 connections) — `core/tests/test_cloud_integration.py`

## Relationships

- [Job Explain & S3 Offload](Job_Explain_%26_S3_Offload.md) (19 shared connections)
- [DynamoDB RunStore Adapter](DynamoDB_RunStore_Adapter.md) (13 shared connections)
- [Run State Rendering](Run_State_Rendering.md) (7 shared connections)
- [Cloud Boto3 Guards & EventLog](Cloud_Boto3_Guards_%26_EventLog.md) (2 shared connections)
- [S3 Result Store](S3_Result_Store.md) (2 shared connections)

## Source Files

- `core/tests/test_cloud_integration.py`

## Audit Trail

- EXTRACTED: 87 (100%)
- INFERRED: 0 (0%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*