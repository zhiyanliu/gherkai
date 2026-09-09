# Fargate Engine Adapter

> 22 nodes · cohesion 0.14

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
- **test_runtask_injects_extra_env()** (3 connections) — `core/tests/test_fargate_engine.py`
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

- [Engine Ports & Adapters](Engine_Ports_%26_Adapters.md) (8 shared connections)
- [Fargate Engine Unit Tests](Fargate_Engine_Unit_Tests.md) (5 shared connections)
- [S3 ReportStore & Subprocess Engine](S3_ReportStore_%26_Subprocess_Engine.md) (5 shared connections)
- [Event Formatting & Cost Model](Event_Formatting_%26_Cost_Model.md) (2 shared connections)
- [Composition Root Wiring](Composition_Root_Wiring.md) (2 shared connections)
- [Fargate Event Drain & Exit Codes](Fargate_Event_Drain_%26_Exit_Codes.md) (1 shared connections)
- [Run State Rendering & Boto Guard](Run_State_Rendering_%26_Boto_Guard.md) (1 shared connections)
- [Job Serialization & E2E Harness](Job_Serialization_%26_E2E_Harness.md) (1 shared connections)
- [Cloud Launcher & DDB EventLog](Cloud_Launcher_%26_DDB_EventLog.md) (1 shared connections)
- [Worker Exit Code Translation](Worker_Exit_Code_Translation.md) (1 shared connections)
- [Fargate Worker Handle](Fargate_Worker_Handle.md) (1 shared connections)

## Source Files

- `core/gherkai_core/adapters/fargate_engine.py`
- `core/tests/test_fargate_engine.py`

## Audit Trail

- EXTRACTED: 47 (78%)
- INFERRED: 13 (22%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*