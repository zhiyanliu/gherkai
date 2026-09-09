# S3 ReportStore & Subprocess Engine

> 33 nodes · cohesion 0.07

## Key Concepts

- **S3ReportStore** (20 connections) — `core/gherkai_core/adapters/report_store/s3.py`
- **SubprocessEngine** (19 connections) — `core/gherkai_core/adapters/subprocess_engine.py`
- **_UnavailableEngine** (15 connections) — `runtime/gherkai_runtime/compose.py`
- **WorkerNotFoundError** (15 connections) — `runtime/gherkai_runtime/compose.py`
- **WorkerSelfDescribeError** (15 connections) — `runtime/gherkai_runtime/compose.py`
- **CloudTarget** (14 connections) — `runtime/gherkai_runtime/compose.py`
- **WorkerCmd** (13 connections) — `runtime/gherkai_runtime/compose.py`
- **_ask_worker()** (8 connections) — `runtime/gherkai_runtime/compose.py`
- **.__init__()** (3 connections) — `core/gherkai_core/adapters/report_store/s3.py`
- **RuntimeError** (3 connections)
- **.__init__()** (3 connections) — `runtime/gherkai_runtime/compose.py`
- **.preflight()** (2 connections) — `core/gherkai_core/adapters/report_store/s3.py`
- **.cwd()** (2 connections) — `core/gherkai_core/adapters/subprocess_engine.py`
- **.detached_chain_lambdas()** (2 connections) — `runtime/gherkai_runtime/compose.py`
- **Exception** (2 connections)
- **.__init__()** (2 connections) — `runtime/gherkai_runtime/compose.py`
- **.__init__()** (2 connections) — `runtime/gherkai_runtime/compose.py`
- **.__init__()** (2 connections) — `runtime/gherkai_runtime/compose.py`
- **ReportStore 的 S3 实装（组合根注入 boto3 s3 client + bucket + 可选 key 前缀）。行为对拍…** (1 connections) — `core/gherkai_core/adapters/report_store/s3.py`
- **s3_client：boto3 s3 client（组合根注入；建桶责任在 IaC，adapter 假定桶已存在）。 prefix：可选 key 前缀（如…** (1 connections) — `core/gherkai_core/adapters/report_store/s3.py`
- **探活（ADR 0030 决定七）：begin 前探桶可达，桶不存在/无权限即抛（cli 接住→退 2）。** (1 connections) — `core/gherkai_core/adapters/report_store/s3.py`
- **Engine port 的子进程实现。cmd = 启 worker 的命令行（如 ['uv','run','python','run_scope.py']）。** (1 connections) — `core/gherkai_core/adapters/subprocess_engine.py`
- **worker 的工作目录（只读，供组合根自省，如 list-deterministic 的 dump spawn，ADR 0036）。** (1 connections) — `core/gherkai_core/adapters/subprocess_engine.py`
- **.__init__()** (1 connections) — `core/gherkai_core/adapters/subprocess_engine.py`
- **一个引擎 worker 的拉起方式 = 定位链的解析结果（ADR 0037 决策 3）。 cmd/cwd 直接喂…** (1 connections) — `runtime/gherkai_runtime/compose.py`
- *... and 8 more nodes in this community*

## Relationships

- [Run Result Verdict Model](Run_Result_Verdict_Model.md) (16 shared connections)
- [Composition Root Wiring](Composition_Root_Wiring.md) (12 shared connections)
- [Render & ReportStore Local](Render_%26_ReportStore_Local.md) (9 shared connections)
- [Run State Rendering & Boto Guard](Run_State_Rendering_%26_Boto_Guard.md) (6 shared connections)
- [Feature Planning to Jobs](Feature_Planning_to_Jobs.md) (5 shared connections)
- [S3 Argument Offload](S3_Argument_Offload.md) (5 shared connections)
- [Fargate Engine Adapter](Fargate_Engine_Adapter.md) (5 shared connections)
- [Worker Command Resolution](Worker_Command_Resolution.md) (3 shared connections)
- [Local Stores & Deterministic Query](Local_Stores_%26_Deterministic_Query.md) (3 shared connections)
- [Cloud Adapter Test Fixtures](Cloud_Adapter_Test_Fixtures.md) (2 shared connections)
- [Reconciler Lambda & Timeouts](Reconciler_Lambda_%26_Timeouts.md) (2 shared connections)
- [Subprocess Worker Launcher](Subprocess_Worker_Launcher.md) (2 shared connections)

## Source Files

- `core/gherkai_core/adapters/report_store/s3.py`
- `core/gherkai_core/adapters/subprocess_engine.py`
- `runtime/gherkai_runtime/compose.py`

## Audit Trail

- EXTRACTED: 58 (49%)
- INFERRED: 60 (51%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*