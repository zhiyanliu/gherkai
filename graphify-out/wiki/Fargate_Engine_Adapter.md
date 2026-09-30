# Fargate Engine Adapter

> 25 nodes · cohesion 0.12

## Key Concepts

- **FargateEngine** (24 connections) — `core/gherkai_core/adapters/fargate_engine.py`
- **._read_events()** (11 connections) — `core/gherkai_core/adapters/fargate_engine.py`
- **.run_scope()** (7 connections) — `core/gherkai_core/adapters/fargate_engine.py`
- **TaskProbe** (6 connections) — `core/gherkai_core/adapters/fargate_engine.py`
- **._await_exit_code()** (5 connections) — `core/gherkai_core/adapters/fargate_engine.py`
- **._final_drain()** (5 connections) — `core/gherkai_core/adapters/fargate_engine.py`
- **._probe_task()** (5 connections) — `core/gherkai_core/adapters/fargate_engine.py`
- **._put_job_and_run_task()** (5 connections) — `core/gherkai_core/adapters/fargate_engine.py`
- **._count_missing()** (4 connections) — `core/gherkai_core/adapters/fargate_engine.py`
- **.start_scope()** (4 connections) — `core/gherkai_core/adapters/fargate_engine.py`
- **Event** (3 connections)
- **Job** (3 connections)
- **test_artifact_injection_kwargs_are_mandatory()** (3 connections) — `core/tests/test_fargate_engine.py`
- **.__init__()** (2 connections) — `core/gherkai_core/adapters/fargate_engine.py`
- **NamedTuple** (1 connections)
- **Engine port 的 Fargate 实现（组合根注入 boto3 client + run 级配置）。对称 SubprocessEngine。…** (1 connections) — `core/gherkai_core/adapters/fargate_engine.py`
- **fire-and-forget 起一个 Fargate task 执行 job，返回 task_arn（ADR 0034：无状态批量运行的 Engine…** (1 connections) — `core/gherkai_core/adapters/fargate_engine.py`
- **起一个 Fargate task 执行 job，返回 (句柄, DDB events 事件流迭代器)。对称…** (1 connections) — `core/gherkai_core/adapters/fargate_engine.py`
- **Query events 表增量拉本 scope 事件 → Event 迭代器（对称 subprocess 的 _read_events 读 fd）。…** (1 connections) — `core/gherkai_core/adapters/fargate_engine.py`
- **DescribeTasks 查不到 task 的有界宽限计数：超 `missing_task_grace_polls` 即抛（ADR…** (1 connections) — `core/gherkai_core/adapters/fargate_engine.py`
- **task STOPPED 后的终读：强一致 Query 补最终一致可能还没看到的末尾事件（ADR 0024 读一致性条）。…** (1 connections) — `core/gherkai_core/adapters/fargate_engine.py`
- **DescribeTasks 探一次 task 终态 + 退出码，返回 TaskProbe(stopped, exit_code, missing)（ADR…** (1 connections) — `core/gherkai_core/adapters/fargate_engine.py`
- **轮询 DescribeTasks 直到拿到确定的 exitCode——scope_done 后读退出码用（ADR 0024「事件流结束信号」）。…** (1 connections) — `core/gherkai_core/adapters/fargate_engine.py`
- **一次 DescribeTasks 探测的结果——**三个正交事实各自命名**（ADR 0024「exitCode 落值延迟」；前两个见下、第三个…** (1 connections) — `core/gherkai_core/adapters/fargate_engine.py`
- **产物落点两参数**必给关键字、无缺省**：cloud 下两者必注，漏传即静默丢产物（实际运行暴露过一次）。 与 ADR 0038 的显式 revision…** (1 connections) — `core/tests/test_fargate_engine.py`

## Relationships

- [Fargate Engine Tests](Fargate_Engine_Tests.md) (4 shared connections)
- [Event Wire Serialization](Event_Wire_Serialization.md) (4 shared connections)
- [Event Gap Grace Tests](Event_Gap_Grace_Tests.md) (3 shared connections)
- [ECS Task Exit Probing](ECS_Task_Exit_Probing.md) (2 shared connections)
- [Core Adapters Documentation](Core_Adapters_Documentation.md) (2 shared connections)
- [Run Definition Domain Model](Run_Definition_Domain_Model.md) (2 shared connections)
- [Worker Log Event Formatting](Worker_Log_Event_Formatting.md) (2 shared connections)
- [Fargate Worker Handle](Fargate_Worker_Handle.md) (2 shared connections)
- [Worker Exit Drain Tests](Worker_Exit_Drain_Tests.md) (1 shared connections)
- [Boto3 Adapter Guard](Boto3_Adapter_Guard.md) (1 shared connections)
- [Event Keys & Exit Records](Event_Keys_%26_Exit_Records.md) (1 shared connections)

## Source Files

- `core/gherkai_core/adapters/fargate_engine.py`
- `core/tests/test_fargate_engine.py`

## Audit Trail

- EXTRACTED: 53 (87%)
- INFERRED: 8 (13%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*