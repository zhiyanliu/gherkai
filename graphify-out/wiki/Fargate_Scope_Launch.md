# Fargate Scope Launch

> 6 nodes · cohesion 0.47

## Key Concepts

- **.run_scope()** (7 connections) — `core/gherkai_core/adapters/fargate_engine.py`
- **._put_job_and_run_task()** (5 connections) — `core/gherkai_core/adapters/fargate_engine.py`
- **.start_scope()** (4 connections) — `core/gherkai_core/adapters/fargate_engine.py`
- **Job** (3 connections)
- **fire-and-forget 起一个 Fargate task 执行 job，返回 task_arn（ADR 0034：无状态批量运行的 Engine…** (1 connections) — `core/gherkai_core/adapters/fargate_engine.py`
- **起一个 Fargate task 执行 job，返回 (句柄, DDB events 事件流迭代器)。对称…** (1 connections) — `core/gherkai_core/adapters/fargate_engine.py`

## Relationships

- [Cloud Launcher & Fargate Adapters](Cloud_Launcher_%26_Fargate_Adapters.md) (3 shared connections)
- [Fargate Task Polling](Fargate_Task_Polling.md) (2 shared connections)
- [Job Serialization](Job_Serialization.md) (1 shared connections)
- [Job/Scenario Explain Model](Job-Scenario_Explain_Model.md) (1 shared connections)

## Source Files

- `core/gherkai_core/adapters/fargate_engine.py`

## Audit Trail

- EXTRACTED: 14 (100%)
- INFERRED: 0 (0%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*