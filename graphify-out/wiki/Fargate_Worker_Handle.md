# Fargate Worker Handle

> 5 nodes · cohesion 0.40

## Key Concepts

- **FargateWorkerHandle** (10 connections) — `core/gherkai_core/adapters/fargate_engine.py`
- **.stop()** (2 connections) — `core/gherkai_core/adapters/fargate_engine.py`
- **.__init__()** (1 connections) — `core/gherkai_core/adapters/fargate_engine.py`
- **一个在跑的 Fargate task 的句柄。stop() 翻成 StopTask（ADR 0026 机制层，对称…** (1 connections) — `core/gherkai_core/adapters/fargate_engine.py`
- **请求优雅停止 = StopTask。 **grace_period_s 在 Fargate 上无法逐次传**（ADR 0024/0032）：容器…** (1 connections) — `core/gherkai_core/adapters/fargate_engine.py`

## Relationships

- [Engine Ports & Adapters](Engine_Ports_%26_Adapters.md) (4 shared connections)
- [Fargate Engine Adapter](Fargate_Engine_Adapter.md) (1 shared connections)
- [Fargate Engine Unit Tests](Fargate_Engine_Unit_Tests.md) (1 shared connections)
- [Event Formatting & Cost Model](Event_Formatting_%26_Cost_Model.md) (1 shared connections)

## Source Files

- `core/gherkai_core/adapters/fargate_engine.py`

## Audit Trail

- EXTRACTED: 7 (64%)
- INFERRED: 4 (36%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*