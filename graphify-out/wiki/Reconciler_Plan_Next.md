# Reconciler Plan Next

> 8 nodes · cohesion 0.29

## Key Concepts

- **Action** (21 connections) — `core/gherkai_core/project.py`
- **plan_next()** (11 connections) — `core/gherkai_core/project.py`
- **test_plan_next_finalize_when_all_terminal()** (8 connections) — `core/tests/test_project.py`
- **test_plan_next_starts_up_to_concurrency()** (5 connections) — `core/tests/test_project.py`
- **reconciler 的建议动作（ADR 0034）——纯数据，adapter 侧据此做副作用（CAS/RunTask/finalize）。…** (1 connections) — `core/gherkai_core/project.py`
- **据当前 RunState 提议下一步动作（ADR 0034 机制四，纯函数、无副作用）。 - 若所有 job 达终态（无 pending/running）→…** (1 connections) — `core/gherkai_core/project.py`
- **全 pending、max_concurrency=2 → 提议 start 前 2 个。** (1 connections) — `core/tests/test_project.py`
- **所有 job 达终态（无 pending/running）→ 提议 finalize。** (1 connections) — `core/tests/test_project.py`

## Relationships

- [Event Records Projection](Event_Records_Projection.md) (11 shared connections)
- [Result Tree Text Rendering](Result_Tree_Text_Rendering.md) (7 shared connections)
- [Worker Log Event Formatting](Worker_Log_Event_Formatting.md) (4 shared connections)
- [State Projection Tests](State_Projection_Tests.md) (3 shared connections)
- [Run Definition Domain Model](Run_Definition_Domain_Model.md) (2 shared connections)
- [Run State Rendering](Run_State_Rendering.md) (2 shared connections)
- [DynamoDB Run Store](DynamoDB_Run_Store.md) (1 shared connections)
- [Event Wire Serialization](Event_Wire_Serialization.md) (1 shared connections)
- [Reconcile Tick and Report](Reconcile_Tick_and_Report.md) (1 shared connections)
- [Core Adapters Documentation](Core_Adapters_Documentation.md) (1 shared connections)

## Source Files

- `core/gherkai_core/project.py`
- `core/tests/test_project.py`

## Audit Trail

- EXTRACTED: 25 (61%)
- INFERRED: 16 (39%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*