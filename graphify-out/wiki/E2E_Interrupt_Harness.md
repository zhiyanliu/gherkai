# E2E Interrupt Harness

> 15 nodes · cohesion 0.18

## Key Concepts

- **e2e_harness.py** (16 connections) — `tools/e2e_harness.py`
- **run()** (8 connections) — `tools/e2e_harness.py`
- **build_job()** (6 connections) — `tools/e2e_harness.py`
- **scrubbed_environ()** (5 connections) — `runtime/gherkai_runtime/compose.py`
- **worker_cmd()** (4 connections) — `tools/e2e_harness.py`
- **snapshot_disk()** (3 connections) — `tools/e2e_harness.py`
- **--interrupt 中断时机矩阵** (2 connections) — `tools/e2e_harness.md`
- **Path** (2 connections)
- **snapshot_s3()** (2 connections) — `tools/e2e_harness.py`
- **ADR 0025 @scope: tag 分组** (1 connections) — `tools/e2e_harness.md`
- **ADR 0032 Fargate 中断丢失量级与真容器 grace 校准** (1 connections) — `tools/e2e_harness.md`
- **继承一份 os.environ、抹掉组合根拥有的那些键（见 `_COMPOSE_OWNED_WORKER_ENV`）——所有注入 env 的起手式。…** (1 connections) — `runtime/gherkai_runtime/compose.py`
- **复用真实 plan 链路生成 job（不手搓 JSON，防 schema 漂移）。 取**匹配 `--engine` 的第一个 job** 作靶子（回退…** (1 connections) — `tools/e2e_harness.py`
- **worker 拉起命令走 `gherkai_runtime.compose.resolve_worker_cmd` 的定位链（ADR 0037 决策…** (1 connections) — `tools/e2e_harness.py`
- **harness 报告判读要点（sample_valid 先于 n_lost）** (1 connections) — `tools/e2e_harness.md`

## Relationships

- [Feature Parsing & Errors](Feature_Parsing_%26_Errors.md) (4 shared connections)
- [Cloud Store Composition Root](Cloud_Store_Composition_Root.md) (2 shared connections)
- [Core Library Concepts & ADRs](Core_Library_Concepts_%26_ADRs.md) (2 shared connections)
- [Worker Command Resolution Chain](Worker_Command_Resolution_Chain.md) (2 shared connections)
- [Worker Capability Queries](Worker_Capability_Queries.md) (1 shared connections)
- [Engine Composition Helpers](Engine_Composition_Helpers.md) (1 shared connections)
- [Job/Scenario Explain Model](Job-Scenario_Explain_Model.md) (1 shared connections)
- [Shared Feature Scope ADRs](Shared_Feature_Scope_ADRs.md) (1 shared connections)
- [Plan Scope/Engine Validation Tests](Plan_Scope-Engine_Validation_Tests.md) (1 shared connections)
- [Job Serialization](Job_Serialization.md) (1 shared connections)

## Source Files

- `runtime/gherkai_runtime/compose.py`
- `tools/e2e_harness.md`
- `tools/e2e_harness.py`

## Audit Trail

- EXTRACTED: 35 (100%)
- INFERRED: 0 (0%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*