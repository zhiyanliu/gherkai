# Job JSON Serialization

> 12 nodes · cohesion 0.18

## Key Concepts

- **job_to_json()** (9 connections) — `core/gherkai_core/wire.py`
- **job_to_line()** (9 connections) — `core/gherkai_core/wire.py`
- **_scenario_to_json()** (4 connections) — `core/gherkai_core/wire.py`
- **_step_to_json()** (4 connections) — `core/gherkai_core/wire.py`
- **_argument_to_json()** (3 connections) — `core/gherkai_core/wire.py`
- **test_job_to_json_assertion_votes_passthrough()** (3 connections) — `core/tests/test_wire.py`
- **Job** (2 connections)
- **Scenario** (1 connections)
- **Step** (1 connections)
- **StepArgument** (1 connections)
- **Job → JSON dict（喂 worker stdin，ADR 0024 输入形状）。** (1 connections) — `core/gherkai_core/wire.py`
- **Job → 单行 JSON 字符串（写 worker stdin）。** (1 connections) — `core/gherkai_core/wire.py`

## Relationships

- [Engine Ports & Adapters](Engine_Ports_%26_Adapters.md) (10 shared connections)
- [Event Progress Formatting](Event_Progress_Formatting.md) (2 shared connections)
- [Fargate Engine](Fargate_Engine.md) (1 shared connections)
- [Subprocess Worker Handle](Subprocess_Worker_Handle.md) (1 shared connections)
- [Feature Planning](Feature_Planning.md) (1 shared connections)

## Source Files

- `core/gherkai_core/wire.py`
- `core/tests/test_wire.py`

## Audit Trail

- EXTRACTED: 27 (100%)
- INFERRED: 0 (0%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*