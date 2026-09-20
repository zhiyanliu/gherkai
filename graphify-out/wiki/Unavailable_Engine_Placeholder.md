# Unavailable Engine Placeholder

> 6 nodes · cohesion 0.33

## Key Concepts

- **_UnavailableEngine** (15 connections) — `runtime/gherkai_runtime/compose.py`
- **Exception** (2 connections)
- **.__init__()** (2 connections) — `runtime/gherkai_runtime/compose.py`
- **某引擎这次装配不出来时的「一用即抛」空占位项——两个后端共用（local: ADR 0037 决策 3；cloud: ADR 0038）。 存在的理由：两个…** (1 connections) — `runtime/gherkai_runtime/compose.py`
- **.run_scope()** (1 connections) — `runtime/gherkai_runtime/compose.py`
- **.start_scope()** (1 connections) — `runtime/gherkai_runtime/compose.py`

## Relationships

- [SSM Paths & Composition Root](SSM_Paths_%26_Composition_Root.md) (2 shared connections)
- [S3 Result Store Port](S3_Result_Store_Port.md) (2 shared connections)
- [Run State Rendering](Run_State_Rendering.md) (2 shared connections)
- [Subprocess Engine Launcher](Subprocess_Engine_Launcher.md) (1 shared connections)
- [Plan Job Generation](Plan_Job_Generation.md) (1 shared connections)
- [Local Report Store](Local_Report_Store.md) (1 shared connections)
- [S3 Report Store](S3_Report_Store.md) (1 shared connections)
- [Run Metadata & S3 Offload](Run_Metadata_%26_S3_Offload.md) (1 shared connections)
- [Fargate Engine Adapter](Fargate_Engine_Adapter.md) (1 shared connections)

## Source Files

- `runtime/gherkai_runtime/compose.py`

## Audit Trail

- EXTRACTED: 7 (41%)
- INFERRED: 10 (59%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*