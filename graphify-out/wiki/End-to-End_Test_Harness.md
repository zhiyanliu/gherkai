# End-to-End Test Harness

> 9 nodes · cohesion 0.33

## Key Concepts

- **e2e_harness.py** (7 connections) — `tools/e2e_harness.py`
- **build_job()** (6 connections) — `tools/e2e_harness.py`
- **run()** (6 connections) — `tools/e2e_harness.py`
- **worker_cmd()** (4 connections) — `tools/e2e_harness.py`
- **snapshot_disk()** (3 connections) — `tools/e2e_harness.py`
- **snapshot_s3()** (2 connections) — `tools/e2e_harness.py`
- **Path** (1 connections)
- **复用真实 plan 链路生成 job（不手搓 JSON，防 schema 漂移）。 取**匹配 `--engine` 的第一个 job** 作靶子（回退…** (1 connections) — `tools/e2e_harness.py`
- **worker 拉起命令走 `gherkai_runtime.compose.resolve_worker_cmd` 的定位链（ADR 0037 决策…** (1 connections) — `tools/e2e_harness.py`

## Relationships

- [Feature Plan to Jobs](Feature_Plan_to_Jobs.md) (3 shared connections)
- [Cloud Boto3 Guards & EventLog](Cloud_Boto3_Guards_%26_EventLog.md) (2 shared connections)
- [Scope Parsing & Plan Errors](Scope_Parsing_%26_Plan_Errors.md) (1 shared connections)
- [Cloud Target & Worker Resolution](Cloud_Target_%26_Worker_Resolution.md) (1 shared connections)

## Source Files

- `tools/e2e_harness.py`

## Audit Trail

- EXTRACTED: 18 (95%)
- INFERRED: 1 (5%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*