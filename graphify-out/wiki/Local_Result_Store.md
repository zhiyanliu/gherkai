# Local Result Store

> 11 nodes · cohesion 0.22

## Key Concepts

- **test_local_result_store_atomic.py** (13 connections) — `core/tests/test_local_result_store_atomic.py`
- **result_store/local.py** (12 connections) — `core/gherkai_core/adapters/result_store/local.py`
- **_big_job_result()** (9 connections) — `core/tests/test_local_result_store_atomic.py`
- **test_job_result_file_stays_readable_by_others()** (4 connections) — `core/tests/test_local_result_store_atomic.py`
- **result_store/__init__.py** (3 connections) — `core/gherkai_core/adapters/result_store/__init__.py`
- **test_concurrent_reader_never_sees_torn_job_result()** (3 connections) — `core/tests/test_local_result_store_atomic.py`
- **ResultStore adapters（ADR 0016）：local（本包 `local.py`）+ S3（`s3.py`，ADR 0030 决定六）。…** (1 connections) — `core/gherkai_core/adapters/result_store/__init__.py`
- **LocalResultStore（ADR 0016 数据面）：每 job 的判定结果追加落盘成单独 JSON。 数据面（追加为主）：一次 run 的每个…** (1 connections) — `core/gherkai_core/adapters/result_store/local.py`
- **LocalResultStore 写面的原子性（ADR 0042 决策四 / 0034）：`explain` 被允许在 run 运行到一半时读…** (1 connections) — `core/tests/test_local_result_store_atomic.py`
- **~几十 KB 的 JobResult（6 scenario × 8 step + 每 step 的 evidence ref 与失败原文），给读者足够撞窗机会。** (1 connections) — `core/tests/test_local_result_store_atomic.py`
- **判定真值的消费者是 CI/人（ADR 0034 表）：原子写用的临时文件是 0600，落盘后必须仍是可被别的用户读的权限。** (1 connections) — `core/tests/test_local_result_store_atomic.py`

## Relationships

- [S3 Result Store](S3_Result_Store.md) (6 shared connections)
- [Local Result Store & Persistence](Local_Result_Store_%26_Persistence.md) (5 shared connections)
- [Result Rendering & Explain](Result_Rendering_%26_Explain.md) (4 shared connections)
- [Cloud Launcher & Fargate Adapters](Cloud_Launcher_%26_Fargate_Adapters.md) (3 shared connections)
- [Atomic Local File Writes](Atomic_Local_File_Writes.md) (2 shared connections)
- [Job/Scenario Explain Model](Job-Scenario_Explain_Model.md) (2 shared connections)
- [Local Report Store](Local_Report_Store.md) (2 shared connections)
- [Job State Serialization](Job_State_Serialization.md) (1 shared connections)

## Source Files

- `core/gherkai_core/adapters/result_store/__init__.py`
- `core/gherkai_core/adapters/result_store/local.py`
- `core/tests/test_local_result_store_atomic.py`

## Audit Trail

- EXTRACTED: 37 (100%)
- INFERRED: 0 (0%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*