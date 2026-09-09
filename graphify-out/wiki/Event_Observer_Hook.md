# Event Observer Hook

> 3 nodes · cohesion 0.67

## Key Concepts

- **.on_event()** (5 connections) — `core/gherkai_core/persist.py`
- **Event** (1 connections)
- **事件旁路观察者（注入 schedule 的 on_event，在 sink_lock **之外**调，ADR 0030 决定三）： 收…** (1 connections) — `core/gherkai_core/persist.py`

## Relationships

- [DynamoDB RunStore Conditional Writes](DynamoDB_RunStore_Conditional_Writes.md) (1 shared connections)
- [Run Persistence Orchestration](Run_Persistence_Orchestration.md) (1 shared connections)
- [Event Formatting & Cost Model](Event_Formatting_%26_Cost_Model.md) (1 shared connections)

## Source Files

- `core/gherkai_core/persist.py`

## Audit Trail

- EXTRACTED: 4 (80%)
- INFERRED: 1 (20%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*