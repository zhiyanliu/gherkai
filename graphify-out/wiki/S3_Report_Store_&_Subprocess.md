# S3 Report Store & Subprocess

> 32 nodes · cohesion 0.08

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
- **.__init__()** (3 connections) — `runtime/gherkai_runtime/detached.py`
- **.preflight()** (2 connections) — `core/gherkai_core/adapters/report_store/s3.py`
- **.cwd()** (2 connections) — `core/gherkai_core/adapters/subprocess_engine.py`
- **.detached_chain_lambdas()** (2 connections) — `runtime/gherkai_runtime/compose.py`
- **.__init__()** (2 connections) — `runtime/gherkai_runtime/compose.py`
- **.__init__()** (2 connections) — `runtime/gherkai_runtime/compose.py`
- **ReportStore 的 S3 实装（组合根注入 boto3 s3 client + bucket + 可选 key 前缀）。行为对拍…** (1 connections) — `core/gherkai_core/adapters/report_store/s3.py`
- **s3_client：boto3 s3 client（组合根注入；建桶责任在 IaC，adapter 假定桶已存在）。 prefix：可选 key 前缀（如…** (1 connections) — `core/gherkai_core/adapters/report_store/s3.py`
- **探活（ADR 0030 决定七）：begin 前探桶可达，桶不存在/无权限即抛（cli 接住→退 2）。** (1 connections) — `core/gherkai_core/adapters/report_store/s3.py`
- **Engine port 的子进程实现。cmd = 启 worker 的命令行（如 ['uv','run','python','run_scope.py']）。** (1 connections) — `core/gherkai_core/adapters/subprocess_engine.py`
- **worker 的工作目录（只读，供组合根自省，如 list-deterministic 的 dump spawn，ADR 0036）。** (1 connections) — `core/gherkai_core/adapters/subprocess_engine.py`
- **.__init__()** (1 connections) — `core/gherkai_core/adapters/subprocess_engine.py`
- **一个引擎 worker 的拉起方式 = 定位链的解析结果（ADR 0037 决策 3）。 cmd/cwd 直接喂…** (1 connections) — `runtime/gherkai_runtime/compose.py`
- **worker **起来了但自述失败**（非零退出）——与「定位不到」（WorkerNotFoundError）是两回事：最常见成因是使用方 `steps/`…** (1 connections) — `runtime/gherkai_runtime/compose.py`
- *... and 7 more nodes in this community*

## Relationships

- [Run Result Rendering](Run_Result_Rendering.md) (21 shared connections)
- [SSM Path & Client Composition](SSM_Path_%26_Client_Composition.md) (12 shared connections)
- [Feature Planning](Feature_Planning.md) (5 shared connections)
- [Report Refs & Results](Report_Refs_%26_Results.md) (5 shared connections)
- [S3 Argument Offloader](S3_Argument_Offloader.md) (5 shared connections)
- [Fargate Engine](Fargate_Engine.md) (5 shared connections)
- [Cloud Target Resolution](Cloud_Target_Resolution.md) (4 shared connections)
- [Local Run Store](Local_Run_Store.md) (3 shared connections)
- [Store Composition & Step Query](Store_Composition_%26_Step_Query.md) (3 shared connections)
- [Cloud Test Fixtures](Cloud_Test_Fixtures.md) (2 shared connections)
- [S3 Report Store Tests](S3_Report_Store_Tests.md) (2 shared connections)
- [Local Report Store](Local_Report_Store.md) (2 shared connections)

## Source Files

- `core/gherkai_core/adapters/report_store/s3.py`
- `core/gherkai_core/adapters/subprocess_engine.py`
- `runtime/gherkai_runtime/compose.py`
- `runtime/gherkai_runtime/detached.py`

## Audit Trail

- EXTRACTED: 58 (49%)
- INFERRED: 60 (51%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*