# Job Serialization & E2E Harness

> 15 nodes · cohesion 0.18

## Key Concepts

- **job_to_json()** (9 connections) — `core/gherkai_core/wire.py`
- **job_to_line()** (9 connections) — `core/gherkai_core/wire.py`
- **e2e_harness.py** (7 connections) — `tools/e2e_harness.py`
- **build_job()** (6 connections) — `tools/e2e_harness.py`
- **run()** (6 connections) — `tools/e2e_harness.py`
- **worker_cmd()** (4 connections) — `tools/e2e_harness.py`
- **test_job_to_json_assertion_votes_passthrough()** (3 connections) — `core/tests/test_wire.py`
- **snapshot_disk()** (3 connections) — `tools/e2e_harness.py`
- **Job** (2 connections)
- **snapshot_s3()** (2 connections) — `tools/e2e_harness.py`
- **Job → JSON dict（喂 worker stdin，ADR 0024 输入形状）。** (1 connections) — `core/gherkai_core/wire.py`
- **Job → 单行 JSON 字符串（写 worker stdin）。** (1 connections) — `core/gherkai_core/wire.py`
- **Path** (1 connections)
- **复用真实 plan 链路生成 job（不手搓 JSON，防 schema 漂移）。 取**匹配 `--engine` 的第一个 job** 作靶子（回退…** (1 connections) — `tools/e2e_harness.py`
- **worker 拉起命令走 `gherkai_runtime.compose.resolve_worker_cmd` 的定位链（ADR 0037 决策…** (1 connections) — `tools/e2e_harness.py`

## Relationships

- [Engine Ports & Adapters](Engine_Ports_%26_Adapters.md) (9 shared connections)
- [Feature Planning to Jobs](Feature_Planning_to_Jobs.md) (3 shared connections)
- [Wire Protocol Serialization](Wire_Protocol_Serialization.md) (2 shared connections)
- [Scenario JSON Serialization](Scenario_JSON_Serialization.md) (1 shared connections)
- [Fargate Engine Adapter](Fargate_Engine_Adapter.md) (1 shared connections)
- [Subprocess Worker Handle](Subprocess_Worker_Handle.md) (1 shared connections)
- [Worker Command Resolution](Worker_Command_Resolution.md) (1 shared connections)

## Source Files

- `core/gherkai_core/wire.py`
- `core/tests/test_wire.py`
- `tools/e2e_harness.py`

## Audit Trail

- EXTRACTED: 36 (97%)
- INFERRED: 1 (3%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*