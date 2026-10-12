# Job Serialization

> 6 nodes · cohesion 0.40

## Key Concepts

- **job_to_json()** (9 connections) — `core/gherkai_core/wire.py`
- **job_to_line()** (9 connections) — `core/gherkai_core/wire.py`
- **test_job_to_json_assertion_votes_passthrough()** (3 connections) — `core/tests/test_wire.py`
- **Job** (2 connections)
- **Job → JSON dict（喂 worker stdin，ADR 0024 输入形状）。** (1 connections) — `core/gherkai_core/wire.py`
- **Job → 单行 JSON 字符串（写 worker stdin）。** (1 connections) — `core/gherkai_core/wire.py`

## Relationships

- [Job/Scenario Explain Model](Job-Scenario_Explain_Model.md) (5 shared connections)
- [Wire Protocol Serialization](Wire_Protocol_Serialization.md) (2 shared connections)
- [Scenario JSON Serialization](Scenario_JSON_Serialization.md) (1 shared connections)
- [Fargate Scope Launch](Fargate_Scope_Launch.md) (1 shared connections)
- [Subprocess Worker Handle](Subprocess_Worker_Handle.md) (1 shared connections)
- [E2E Interrupt Harness](E2E_Interrupt_Harness.md) (1 shared connections)
- [Cloud Launcher & Fargate Adapters](Cloud_Launcher_%26_Fargate_Adapters.md) (1 shared connections)
- [SQLite Event Log Adapter](SQLite_Event_Log_Adapter.md) (1 shared connections)

## Source Files

- `core/gherkai_core/wire.py`
- `core/tests/test_wire.py`

## Audit Trail

- EXTRACTED: 19 (100%)
- INFERRED: 0 (0%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*