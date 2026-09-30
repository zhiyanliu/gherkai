# Projected Run Status

> 6 nodes · cohesion 0.33

## Key Concepts

- **projected_run_status()** (10 connections) — `core/gherkai_core/project.py`
- **test_projected_run_status_ignores_aggregate_value_from_project()** (5 connections) — `core/tests/test_project.py`
- **test_projected_run_status_pending_only_while_all_jobs_pending()** (4 connections) — `core/tests/test_project.py`
- **投影写该落库的 run 级 status（ADR 0034 机制三）：投影里全 job 仍 pending → `pending`，否则 `running`。…** (1 connections) — `core/gherkai_core/project.py`
- **全 job pending → pending（run 还没起过任何 job）；任一 job 推进 → running；恒非终态（终态归 finalize）。** (1 connections) — `core/tests/test_project.py`
- **判据只看 job 态：project() 的 run 级 status 是终态聚合值（零事件的全 pending run 也吐 PASSED）， 喂它的…** (1 connections) — `core/tests/test_project.py`

## Relationships

- [Event Records Projection](Event_Records_Projection.md) (4 shared connections)
- [Run State Rendering](Run_State_Rendering.md) (3 shared connections)
- [DynamoDB Run Store](DynamoDB_Run_Store.md) (2 shared connections)
- [Result Tree Text Rendering](Result_Tree_Text_Rendering.md) (2 shared connections)
- [State Projection Tests](State_Projection_Tests.md) (1 shared connections)

## Source Files

- `core/gherkai_core/project.py`
- `core/tests/test_project.py`

## Audit Trail

- EXTRACTED: 17 (100%)
- INFERRED: 0 (0%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*