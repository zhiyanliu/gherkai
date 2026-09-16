# Worker Scope Runner Port

> 5 nodes · cohesion 0.40

## Key Concepts

- **.run_scope()** (5 connections) — `core/gherkai_core/ports.py`
- **Event** (2 connections)
- **.__call__()** (2 connections) — `core/gherkai_core/ports.py`
- **Job** (1 connections)
- **起一个 worker 跑这个 job，返回 (句柄, ADR 0024 事件流迭代器)。 事件流逐条产出（ADR 0024 流式）；迭代结束 = worker…** (1 connections) — `core/gherkai_core/ports.py`

## Relationships

- [Run State Rendering](Run_State_Rendering.md) (1 shared connections)
- [S3 Report Store & Control Plane](S3_Report_Store_%26_Control_Plane.md) (1 shared connections)
- [Cloud Boto3 Guards & EventLog](Cloud_Boto3_Guards_%26_EventLog.md) (1 shared connections)

## Source Files

- `core/gherkai_core/ports.py`

## Audit Trail

- EXTRACTED: 7 (100%)
- INFERRED: 0 (0%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*