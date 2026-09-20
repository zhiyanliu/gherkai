# Atomic Result Store

> 7 nodes · cohesion 0.38

## Key Concepts

- **test_local_result_store_atomic.py** (13 connections) — `core/tests/test_local_result_store_atomic.py`
- **_big_job_result()** (9 connections) — `core/tests/test_local_result_store_atomic.py`
- **test_job_result_file_stays_readable_by_others()** (4 connections) — `core/tests/test_local_result_store_atomic.py`
- **test_concurrent_reader_never_sees_torn_job_result()** (3 connections) — `core/tests/test_local_result_store_atomic.py`
- **LocalResultStore 写面的原子性（ADR 0042 决策四 / 0034）：`explain` 被允许在 run 运行到一半时读…** (1 connections) — `core/tests/test_local_result_store_atomic.py`
- **~几十 KB 的 JobResult（6 scenario × 8 step + 每 step 的 evidence ref 与失败原文），给读者足够撞窗机会。** (1 connections) — `core/tests/test_local_result_store_atomic.py`
- **判定真值的消费者是 CI/人（ADR 0034 表）：原子写用的临时文件是 0600，落盘后必须仍是可被别的用户读的权限。** (1 connections) — `core/tests/test_local_result_store_atomic.py`

## Relationships

- [Explain Rendering Tests](Explain_Rendering_Tests.md) (4 shared connections)
- [Local Result Store](Local_Result_Store.md) (3 shared connections)
- [Run Metadata & S3 Offload](Run_Metadata_%26_S3_Offload.md) (2 shared connections)
- [S3 Result Store Port](S3_Result_Store_Port.md) (2 shared connections)
- [Local Report Store](Local_Report_Store.md) (2 shared connections)
- [Run State Rendering](Run_State_Rendering.md) (2 shared connections)
- [Local & S3 Result Stores](Local_%26_S3_Result_Stores.md) (1 shared connections)

## Source Files

- `core/tests/test_local_result_store_atomic.py`

## Audit Trail

- EXTRACTED: 24 (100%)
- INFERRED: 0 (0%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*