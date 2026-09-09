# Fargate Engine

> 21 nodes · cohesion 0.15

## Key Concepts

- **FargateEngine** (26 connections) — `core/gherkai_core/adapters/fargate_engine.py`
- **._read_events()** (10 connections) — `core/gherkai_core/adapters/fargate_engine.py`
- **.run_scope()** (7 connections) — `core/gherkai_core/adapters/fargate_engine.py`
- **TaskProbe** (6 connections) — `core/gherkai_core/adapters/fargate_engine.py`
- **._final_drain()** (5 connections) — `core/gherkai_core/adapters/fargate_engine.py`
- **._probe_task()** (5 connections) — `core/gherkai_core/adapters/fargate_engine.py`
- **._put_job_and_run_task()** (5 connections) — `core/gherkai_core/adapters/fargate_engine.py`
- **._await_exit_code()** (4 connections) — `core/gherkai_core/adapters/fargate_engine.py`
- **.start_scope()** (4 connections) — `core/gherkai_core/adapters/fargate_engine.py`
- **Event** (3 connections)
- **Job** (3 connections)
- **.__init__()** (2 connections) — `core/gherkai_core/adapters/fargate_engine.py`
- **fire-and-forget 起一个 Fargate task 跑 job，返回 task_arn（ADR 0034：无状态跑批的 Engine…** (1 connections) — `core/gherkai_core/adapters/fargate_engine.py`
- **起一个 Fargate task 跑 job，返回 (句柄, DDB events 事件流迭代器)。对称…** (1 connections) — `core/gherkai_core/adapters/fargate_engine.py`
- **Query events 表增量拉本 scope 事件 → Event 迭代器（对称 subprocess 的 _read_events 读 fd）。…** (1 connections) — `core/gherkai_core/adapters/fargate_engine.py`
- **task STOPPED 后的终读：强一致 Query 补最终一致可能还没看到的末尾事件（ADR 0024 读一致性条）。…** (1 connections) — `core/gherkai_core/adapters/fargate_engine.py`
- **DescribeTasks 探一次 task 终态 + 退出码，返回 TaskProbe(stopped, exit_code)（ADR…** (1 connections) — `core/gherkai_core/adapters/fargate_engine.py`
- **轮询 DescribeTasks 直到拿到确定的 exitCode——scope_done 后读退出码用（ADR 0024「事件流结束信号」）。…** (1 connections) — `core/gherkai_core/adapters/fargate_engine.py`
- **一次 DescribeTasks 探测的结果——**两个正交事实各自命名**（ADR 0024「exitCode 落值延迟」）： -…** (1 connections) — `core/gherkai_core/adapters/fargate_engine.py`
- **Engine port 的 Fargate 实现（组合根注入 boto3 client + run 级配置）。对称 SubprocessEngine。…** (1 connections) — `core/gherkai_core/adapters/fargate_engine.py`
- **NamedTuple** (1 connections)

## Relationships

- [S3 Report Store & Subprocess](S3_Report_Store_%26_Subprocess.md) (5 shared connections)
- [Engine Ports & Adapters](Engine_Ports_%26_Adapters.md) (4 shared connections)
- [Fargate Engine Tests](Fargate_Engine_Tests.md) (3 shared connections)
- [Fargate Worker Handle](Fargate_Worker_Handle.md) (3 shared connections)
- [Exit Code Await Polling](Exit_Code_Await_Polling.md) (2 shared connections)
- [Event Progress Formatting](Event_Progress_Formatting.md) (2 shared connections)
- [SSM Path & Client Composition](SSM_Path_%26_Client_Composition.md) (2 shared connections)
- [Run Result Rendering](Run_Result_Rendering.md) (2 shared connections)
- [Boto Guard & S3 Offload](Boto_Guard_%26_S3_Offload.md) (1 shared connections)
- [Job JSON Serialization](Job_JSON_Serialization.md) (1 shared connections)
- [Task Exit Event Records](Task_Exit_Event_Records.md) (1 shared connections)
- [Worker Exit Code Mapping](Worker_Exit_Code_Mapping.md) (1 shared connections)

## Source Files

- `core/gherkai_core/adapters/fargate_engine.py`

## Audit Trail

- EXTRACTED: 45 (78%)
- INFERRED: 13 (22%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*