# Capability Registry Self-Description

> 3 nodes · cohesion 0.67

## Key Concepts

- **list_registry()** (5 connections) — `engines/novaact/gherkai_worker_novaact/deterministic.py`
- **test_loads_recursively_in_sorted_order_and_registers()** (4 connections) — `engines/novaact/tests/test_user_steps.py`
- **注册表自述（ADR 0036「2.」）：作自述入口 `--capabilities` 的 `deterministic_steps` 键给 CLI 转述。** (1 connections) — `engines/novaact/gherkai_worker_novaact/deterministic.py`

## Relationships

- [User Steps Loading](User_Steps_Loading.md) (3 shared connections)
- [Deterministic Step Registry](Deterministic_Step_Registry.md) (2 shared connections)
- [Nova Act Worker Package](Nova_Act_Worker_Package.md) (1 shared connections)

## Source Files

- `engines/novaact/gherkai_worker_novaact/deterministic.py`
- `engines/novaact/tests/test_user_steps.py`

## Audit Trail

- EXTRACTED: 8 (100%)
- INFERRED: 0 (0%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*