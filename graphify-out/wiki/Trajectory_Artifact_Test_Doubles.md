# Trajectory Artifact Test Doubles

> 7 nodes · cohesion 0.33

## Key Concepts

- **_TrajNova** (6 connections) — `engines/novaact/tests/test_run_step.py`
- **_TrajResult** (5 connections) — `engines/novaact/tests/test_run_step.py`
- **.act()** (2 connections) — `engines/novaact/tests/test_run_step.py`
- **.act_get()** (2 connections) — `engines/novaact/tests/test_run_step.py`
- **带 trajectory_file_path 的 fake result（.html 不存在 → _collect_traj 回退用 json 路径本身）。** (1 connections) — `engines/novaact/tests/test_run_step.py`
- **.__init__()** (1 connections) — `engines/novaact/tests/test_run_step.py`
- **.__init__()** (1 connections) — `engines/novaact/tests/test_run_step.py`

## Relationships

- [Step Dispatch & Error Mapping](Step_Dispatch_%26_Error_Mapping.md) (4 shared connections)

## Source Files

- `engines/novaact/tests/test_run_step.py`

## Audit Trail

- EXTRACTED: 11 (100%)
- INFERRED: 0 (0%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*