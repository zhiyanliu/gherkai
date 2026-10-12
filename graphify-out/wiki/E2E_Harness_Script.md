# E2E Harness Script

> 16 nodes · cohesion 0.17

## Key Concepts

- **e2e_harness.py** (16 connections) — `tools/e2e_harness.py`
- **run()** (8 connections) — `tools/e2e_harness.py`
- **build_job()** (6 connections) — `tools/e2e_harness.py`
- **scrubbed_environ()** (5 connections) — `runtime/gherkai_runtime/compose.py`
- **worker_cmd()** (4 connections) — `tools/e2e_harness.py`
- **e2e_harness.py（opt-in 手动端到端验证脚本）** (3 connections) — `tools/e2e_harness.md`
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

- [Feature File Parsing](Feature_File_Parsing.md) (6 shared connections)
- [SSM Paths And Compose](SSM_Paths_And_Compose.md) (2 shared connections)
- [Execution Architecture ADRs](Execution_Architecture_ADRs.md) (2 shared connections)
- [AWS Target Resolution](AWS_Target_Resolution.md) (2 shared connections)
- [Store Port Definitions](Store_Port_Definitions.md) (1 shared connections)
- [Local Compose Root](Local_Compose_Root.md) (1 shared connections)
- [Cloud Adapter Boundary Modules](Cloud_Adapter_Boundary_Modules.md) (1 shared connections)
- [Shared Feature Boundary ADRs](Shared_Feature_Boundary_ADRs.md) (1 shared connections)
- [Subprocess Engine Adapter](Subprocess_Engine_Adapter.md) (1 shared connections)

## Source Files

- `runtime/gherkai_runtime/compose.py`
- `tools/e2e_harness.md`
- `tools/e2e_harness.py`

## Audit Trail

- EXTRACTED: 37 (100%)
- INFERRED: 0 (0%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*