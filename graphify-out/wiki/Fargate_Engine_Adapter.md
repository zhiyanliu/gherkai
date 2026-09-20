# Fargate Engine Adapter

> 28 nodes · cohesion 0.11

## Key Concepts

- **FargateEngine** (31 connections) — `core/gherkai_core/adapters/fargate_engine.py`
- **event_from_line()** (15 connections) — `core/gherkai_core/wire.py`
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
- **Event** (2 connections)
- **test_event_from_line()** (2 connections) — `core/tests/test_wire.py`
- **NamedTuple** (1 connections)
- **Engine port 的 Fargate 实现（组合根注入 boto3 client + run 级配置）。对称 SubprocessEngine。…** (1 connections) — `core/gherkai_core/adapters/fargate_engine.py`
- **fire-and-forget 起一个 Fargate task 执行 job，返回 task_arn（ADR 0034：无状态批量运行的 Engine…** (1 connections) — `core/gherkai_core/adapters/fargate_engine.py`
- **起一个 Fargate task 执行 job，返回 (句柄, DDB events 事件流迭代器)。对称…** (1 connections) — `core/gherkai_core/adapters/fargate_engine.py`
- **Query events 表增量拉本 scope 事件 → Event 迭代器（对称 subprocess 的 _read_events 读 fd）。…** (1 connections) — `core/gherkai_core/adapters/fargate_engine.py`
- **DescribeTasks 查不到 task 的有界宽限计数：超 `missing_task_grace_polls` 即抛（ADR…** (1 connections) — `core/gherkai_core/adapters/fargate_engine.py`
- **task STOPPED 后的终读：强一致 Query 补最终一致可能还没看到的末尾事件（ADR 0024 读一致性条）。…** (1 connections) — `core/gherkai_core/adapters/fargate_engine.py`
- **DescribeTasks 探一次 task 终态 + 退出码，返回 TaskProbe(stopped, exit_code, missing)（ADR…** (1 connections) — `core/gherkai_core/adapters/fargate_engine.py`
- **轮询 DescribeTasks 直到拿到确定的 exitCode——scope_done 后读退出码用（ADR 0024「事件流结束信号」）。…** (1 connections) — `core/gherkai_core/adapters/fargate_engine.py`
- *... and 3 more nodes in this community*

## Relationships

- [DynamoDB Event Log](DynamoDB_Event_Log.md) (6 shared connections)
- [Wire Protocol Serialization](Wire_Protocol_Serialization.md) (6 shared connections)
- [Fargate Engine Tests](Fargate_Engine_Tests.md) (4 shared connections)
- [Fargate Worker Handle](Fargate_Worker_Handle.md) (3 shared connections)
- [Fargate Event Read Tests](Fargate_Event_Read_Tests.md) (3 shared connections)
- [Event Progress Formatting](Event_Progress_Formatting.md) (3 shared connections)
- [S3 Report Store](S3_Report_Store.md) (3 shared connections)
- [ECS Task Probe Tests](ECS_Task_Probe_Tests.md) (2 shared connections)
- [Run Metadata & S3 Offload](Run_Metadata_%26_S3_Offload.md) (2 shared connections)
- [SSM Paths & Composition Root](SSM_Paths_%26_Composition_Root.md) (2 shared connections)
- [Subprocess Engine Adapter](Subprocess_Engine_Adapter.md) (2 shared connections)
- [AWS Adapter Clients](AWS_Adapter_Clients.md) (1 shared connections)

## Source Files

- `core/gherkai_core/adapters/fargate_engine.py`
- `core/gherkai_core/wire.py`
- `core/tests/test_fargate_engine.py`
- `core/tests/test_wire.py`

## Audit Trail

- EXTRACTED: 67 (82%)
- INFERRED: 15 (18%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*