# Task Def Stop Timeout

> 9 nodes · cohesion 0.31

## Key Concepts

- **_StopTimeoutEcs** (8 connections) — `runtime/tests/test_compose.py`
- **container_name()** (7 connections) — `runtime/gherkai_runtime/names.py`
- **read_task_def_stop_timeout()** (6 connections) — `runtime/gherkai_runtime/compose.py`
- **test_read_task_def_stop_timeout_none_when_unset_or_container_absent()** (4 connections) — `runtime/tests/test_compose.py`
- **test_read_task_def_stop_timeout_reads_worker_container()** (4 connections) — `runtime/tests/test_compose.py`
- **读某 task-def revision 上 worker container 的 `stopTimeout`（秒），它就是**云端后端真实的停止宽限**。…** (1 connections) — `runtime/gherkai_runtime/compose.py`
- **task-def 里的 container 名（RunTask overrides 指定往哪个 container 注 env）。不带…** (1 connections) — `runtime/gherkai_runtime/names.py`
- **.describe_task_definition()** (1 connections) — `runtime/tests/test_compose.py`
- **.__init__()** (1 connections) — `runtime/tests/test_compose.py`

## Relationships

- [Worker Locator & AWS Resolution](Worker_Locator_%26_AWS_Resolution.md) (3 shared connections)
- [SSM Paths & Composition Root](SSM_Paths_%26_Composition_Root.md) (2 shared connections)
- [Worker Naming & Variants](Worker_Naming_%26_Variants.md) (2 shared connections)
- [Run State Rendering](Run_State_Rendering.md) (2 shared connections)
- [Resource Naming Source](Resource_Naming_Source.md) (1 shared connections)
- [Plan Job Generation](Plan_Job_Generation.md) (1 shared connections)

## Source Files

- `runtime/gherkai_runtime/compose.py`
- `runtime/gherkai_runtime/names.py`
- `runtime/tests/test_compose.py`

## Audit Trail

- EXTRACTED: 19 (86%)
- INFERRED: 3 (14%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*