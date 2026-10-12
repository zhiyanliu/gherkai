# Store Port Definitions

> 35 nodes · cohesion 0.07

## Key Concepts

- **ResultStore** (28 connections) — `core/gherkai_core/ports.py`
- **ReportStore** (22 connections) — `core/gherkai_core/ports.py`
- **_UnavailableEngine** (15 connections) — `runtime/gherkai_runtime/compose.py`
- **WorkerNotFoundError** (15 connections) — `runtime/gherkai_runtime/compose.py`
- **WorkerSelfDescribeError** (15 connections) — `runtime/gherkai_runtime/compose.py`
- **CloudTarget** (14 connections) — `runtime/gherkai_runtime/compose.py`
- **WorkerCmd** (13 connections) — `runtime/gherkai_runtime/compose.py`
- **_ask_worker()** (9 connections) — `runtime/gherkai_runtime/compose.py`
- **.__init__()** (4 connections) — `core/gherkai_core/persist.py`
- **.write()** (4 connections) — `core/gherkai_core/ports.py`
- **RuntimeError** (4 connections)
- **.__init__()** (3 connections) — `runtime/gherkai_runtime/compose.py`
- **.load_all()** (2 connections) — `core/gherkai_core/ports.py`
- **.load_job_result()** (2 connections) — `core/gherkai_core/ports.py`
- **.save_job_result()** (2 connections) — `core/gherkai_core/ports.py`
- **.detached_chain_lambdas()** (2 connections) — `runtime/gherkai_runtime/compose.py`
- **Exception** (2 connections)
- **.__init__()** (2 connections) — `runtime/gherkai_runtime/compose.py`
- **.__init__()** (2 connections) — `runtime/gherkai_runtime/compose.py`
- **.__init__()** (2 connections) — `runtime/gherkai_runtime/compose.py`
- **ResourceUri** (1 connections)
- **数据面：每 job（即 scope）判定真值，追加为主（**判定真值唯一权威**；CI 读判定靠它，ADR 0016）。 local adapter 是…** (1 connections) — `core/gherkai_core/ports.py`
- **归集报告产物为一份**派生只读导航视图**（RunReport，ADR 0027）：manifest.json + index.html。 纯派生：可从…** (1 connections) — `core/gherkai_core/ports.py`
- **从 RunResult 归集出 <report_root>/<run_id>/{manifest.json, index.html}，返回…** (1 connections) — `core/gherkai_core/ports.py`
- **.preflight()** (1 connections) — `core/gherkai_core/ports.py`
- *... and 10 more nodes in this community*

## Relationships

- [Step Argument S3 Offload](Step_Argument_S3_Offload.md) (14 shared connections)
- [Cloud Adapter Boundary Modules](Cloud_Adapter_Boundary_Modules.md) (9 shared connections)
- [Run State Store](Run_State_Store.md) (8 shared connections)
- [SSM Paths And Compose](SSM_Paths_And_Compose.md) (8 shared connections)
- [S3 Result Store](S3_Result_Store.md) (5 shared connections)
- [Subprocess Engine & Launcher](Subprocess_Engine_%26_Launcher.md) (5 shared connections)
- [Feature File Parsing](Feature_File_Parsing.md) (5 shared connections)
- [Explain Reads And Report Store](Explain_Reads_And_Report_Store.md) (5 shared connections)
- [S3 Report Store](S3_Report_Store.md) (5 shared connections)
- [Fargate Engine Adapter](Fargate_Engine_Adapter.md) (5 shared connections)
- [Job Explain Data Model](Job_Explain_Data_Model.md) (4 shared connections)
- [Worker Capability Probing](Worker_Capability_Probing.md) (4 shared connections)

## Source Files

- `core/gherkai_core/persist.py`
- `core/gherkai_core/ports.py`
- `runtime/gherkai_runtime/compose.py`

## Audit Trail

- EXTRACTED: 62 (46%)
- INFERRED: 73 (54%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*