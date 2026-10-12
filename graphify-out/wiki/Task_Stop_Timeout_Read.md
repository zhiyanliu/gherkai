# Task Stop Timeout Read

> 10 nodes · cohesion 0.27

## Key Concepts

- **_StopTimeoutEcs** (8 connections) — `runtime/tests/test_compose.py`
- **container_name()** (7 connections) — `runtime/gherkai_runtime/names.py`
- **read_task_def_stop_timeout()** (6 connections) — `runtime/gherkai_runtime/compose.py`
- **test_read_task_def_stop_timeout_none_when_unset_or_container_absent()** (4 connections) — `runtime/tests/test_compose.py`
- **test_read_task_def_stop_timeout_reads_worker_container()** (4 connections) — `runtime/tests/test_compose.py`
- **test_task_def_and_container_name()** (3 connections) — `runtime/tests/test_compose.py`
- **读某 task-def revision 上 worker container 的 `stopTimeout`（秒），它就是**云端后端真实的停止宽限**。…** (1 connections) — `runtime/gherkai_runtime/compose.py`
- **task-def 里的 container 名（RunTask overrides 指定往哪个 container 注 env）。不带…** (1 connections) — `runtime/gherkai_runtime/names.py`
- **.describe_task_definition()** (1 connections) — `runtime/tests/test_compose.py`
- **.__init__()** (1 connections) — `runtime/tests/test_compose.py`

## Relationships

- [AWS Target & Network Resolution](AWS_Target_%26_Network_Resolution.md) (4 shared connections)
- [Cloud Store Composition Root](Cloud_Store_Composition_Root.md) (2 shared connections)
- [Resource Naming Source](Resource_Naming_Source.md) (2 shared connections)
- [Worker Variant Resolution](Worker_Variant_Resolution.md) (1 shared connections)
- [Feature Parsing & Errors](Feature_Parsing_%26_Errors.md) (1 shared connections)
- [Run State Rendering & DDB Store](Run_State_Rendering_%26_DDB_Store.md) (1 shared connections)
- [Cloud Launcher & Fargate Adapters](Cloud_Launcher_%26_Fargate_Adapters.md) (1 shared connections)

## Source Files

- `runtime/gherkai_runtime/compose.py`
- `runtime/gherkai_runtime/names.py`
- `runtime/tests/test_compose.py`

## Audit Trail

- EXTRACTED: 21 (88%)
- INFERRED: 3 (12%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*