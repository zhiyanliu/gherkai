# Result Store & Report Refs

> 16 nodes · cohesion 0.18

## Key Concepts

- **StepResult** (36 connections) — `core/gherkai_core/model.py`
- **ScenarioResult** (34 connections) — `core/gherkai_core/model.py`
- **ReportRef** (31 connections) — `core/gherkai_core/model.py`
- **test_explain_cloud_reads_evidence_from_s3()** (13 connections) — `cli/tests/test_main.py`
- **test_local_result_store_atomic.py** (13 connections) — `core/tests/test_local_result_store_atomic.py`
- **_big_job_result()** (9 connections) — `core/tests/test_local_result_store_atomic.py`
- **_explain_cloud_stores()** (4 connections) — `cli/tests/test_main.py`
- **test_job_result_file_stays_readable_by_others()** (4 connections) — `core/tests/test_local_result_store_atomic.py`
- **test_concurrent_reader_never_sees_torn_job_result()** (3 connections) — `core/tests/test_local_result_store_atomic.py`
- **假的云端两 store（explain 只读 RunStore/ResultStore）：验接线与读路径，不连真 AWS。** (1 connections) — `cli/tests/test_main.py`
- **云端后端：判定明细经 ResultStore 读回，证据经注入的 s3 client `get_object` 读回（s3:// 解引用路径）。** (1 connections) — `cli/tests/test_main.py`
- **原生报告产物指针（ADR 0027/0024/0010）。core 永远是**不透明搬运**——不读 kind 值、 不 stat/fetch ref、不按…** (1 connections) — `core/gherkai_core/model.py`
- **单个 step 的归约结果（core 保留 step 级粒度，ADR 0024）。 duration_ms 是 step 墙钟时长（core 用…** (1 connections) — `core/gherkai_core/model.py`
- **LocalResultStore 写面的原子性（ADR 0042 决策四 / 0034）：`explain` 被允许在 run 运行到一半时读…** (1 connections) — `core/tests/test_local_result_store_atomic.py`
- **~几十 KB 的 JobResult（6 scenario × 8 step + 每 step 的 evidence ref 与失败原文），给读者足够撞窗机会。** (1 connections) — `core/tests/test_local_result_store_atomic.py`
- **判定真值的消费者是 CI/人（ADR 0034 表）：原子写用的临时文件是 0600，落盘后必须仍是可被别的用户读的权限。** (1 connections) — `core/tests/test_local_result_store_atomic.py`

## Relationships

- [Local Report Store](Local_Report_Store.md) (22 shared connections)
- [Run Result Aggregation Tree](Run_Result_Aggregation_Tree.md) (21 shared connections)
- [Cloud Store Adapters](Cloud_Store_Adapters.md) (16 shared connections)
- [Event Log Adapters](Event_Log_Adapters.md) (14 shared connections)
- [Job Domain Models](Job_Domain_Models.md) (9 shared connections)
- [S3 Report Store Tests](S3_Report_Store_Tests.md) (7 shared connections)
- [Explain Command Tests](Explain_Command_Tests.md) (4 shared connections)
- [Run Scheduling Core](Run_Scheduling_Core.md) (3 shared connections)
- [Local Result Store](Local_Result_Store.md) (3 shared connections)
- [Run State Store](Run_State_Store.md) (2 shared connections)
- [CLI Run Command Tests](CLI_Run_Command_Tests.md) (2 shared connections)
- [Event Formatting](Event_Formatting.md) (2 shared connections)

## Source Files

- `cli/tests/test_main.py`
- `core/gherkai_core/model.py`
- `core/tests/test_local_result_store_atomic.py`

## Audit Trail

- EXTRACTED: 120 (91%)
- INFERRED: 12 (9%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*