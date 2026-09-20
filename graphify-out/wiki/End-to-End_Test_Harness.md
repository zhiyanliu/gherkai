# End-to-End Test Harness

> 9 nodes · cohesion 0.36

## Key Concepts

- **e2e_harness.py** (9 connections) — `tools/e2e_harness.py`
- **run()** (8 connections) — `tools/e2e_harness.py`
- **build_job()** (6 connections) — `tools/e2e_harness.py`
- **worker_cmd()** (4 connections) — `tools/e2e_harness.py`
- **snapshot_disk()** (3 connections) — `tools/e2e_harness.py`
- **Path** (2 connections)
- **snapshot_s3()** (2 connections) — `tools/e2e_harness.py`
- **复用真实 plan 链路生成 job（不手搓 JSON，防 schema 漂移）。 取**匹配 `--engine` 的第一个 job** 作靶子（回退…** (1 connections) — `tools/e2e_harness.py`
- **worker 拉起命令走 `gherkai_runtime.compose.resolve_worker_cmd` 的定位链（ADR 0037 决策…** (1 connections) — `tools/e2e_harness.py`

## Relationships

- [Plan Job Generation](Plan_Job_Generation.md) (3 shared connections)
- [Scope Tag Resolution](Scope_Tag_Resolution.md) (1 shared connections)
- [Event Progress Formatting](Event_Progress_Formatting.md) (1 shared connections)
- [SSM Paths & Composition Root](SSM_Paths_%26_Composition_Root.md) (1 shared connections)
- [Contributor Guardrail Docs](Contributor_Guardrail_Docs.md) (1 shared connections)
- [Engine Composition Root](Engine_Composition_Root.md) (1 shared connections)
- [Wire Protocol Serialization](Wire_Protocol_Serialization.md) (1 shared connections)
- [Worker Locator & AWS Resolution](Worker_Locator_%26_AWS_Resolution.md) (1 shared connections)

## Source Files

- `tools/e2e_harness.py`

## Audit Trail

- EXTRACTED: 23 (100%)
- INFERRED: 0 (0%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*