# Task Definition Stop Timeout

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

- [Cloud Resource Resolution](Cloud_Resource_Resolution.md) (4 shared connections)
- [SSM Path Naming](SSM_Path_Naming.md) (2 shared connections)
- [Resource Naming Source](Resource_Naming_Source.md) (2 shared connections)
- [Worker Variant Resolution](Worker_Variant_Resolution.md) (1 shared connections)
- [Feature Planning Core](Feature_Planning_Core.md) (1 shared connections)
- [Run State Store](Run_State_Store.md) (1 shared connections)
- [Run Result Aggregation Tree](Run_Result_Aggregation_Tree.md) (1 shared connections)

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