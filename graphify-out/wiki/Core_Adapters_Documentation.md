# Core Adapters Documentation

> 62 nodes · cohesion 0.05

## Key Concepts

- **model.py** (80 connections) — `core/gherkai_core/model.py`
- **ports.py** (28 connections) — `core/gherkai_core/ports.py`
- **RunStore** (27 connections) — `core/gherkai_core/ports.py`
- **fargate_engine.py** (23 connections) — `core/gherkai_core/adapters/fargate_engine.py`
- **reconcile.py** (23 connections) — `core/gherkai_core/reconcile.py`
- **ResultStore** (21 connections) — `core/gherkai_core/ports.py`
- **subprocess_engine.py** (18 connections) — `core/gherkai_core/adapters/subprocess_engine.py`
- **persist.py** (18 connections) — `core/gherkai_core/persist.py`
- **ReportStore** (15 connections) — `core/gherkai_core/ports.py`
- **core 包 contributor 文档** (14 connections) — `core/DEVELOPMENT.md`
- **errors.py** (13 connections) — `core/gherkai_core/errors.py`
- **EventLog** (11 connections) — `core/gherkai_core/reconcile.py`
- **Launcher** (9 connections) — `core/gherkai_core/reconcile.py`
- **cloud_launcher.py** (6 connections) — `core/gherkai_core/adapters/cloud_launcher.py`
- **adapters/run_store（local / ddb）** (6 connections) — `core/DEVELOPMENT.md`
- **gherkai-core 发行包入口页** (6 connections) — `core/README.md`
- **.__init__()** (4 connections) — `core/gherkai_core/persist.py`
- **.write()** (4 connections) — `core/gherkai_core/ports.py`
- **载体：三个 Lambda 的部署 asset** (4 connections) — `docs/internals/cloud-backend-carriers.md`
- **.project_state()** (3 connections) — `core/gherkai_core/ports.py`
- **.try_finalize()** (3 connections) — `core/gherkai_core/ports.py`
- **adapters/_atomic.py 原子落盘** (2 connections) — `core/DEVELOPMENT.md`
- **adapters/_boto.py boto3 依赖守卫** (2 connections) — `core/DEVELOPMENT.md`
- **adapters/report_store（local / s3）** (2 connections) — `core/DEVELOPMENT.md`
- **.load_all()** (2 connections) — `core/gherkai_core/ports.py`
- *... and 37 more nodes in this community*

## Relationships

- [Result Tree Text Rendering](Result_Tree_Text_Rendering.md) (44 shared connections)
- [Run Definition Domain Model](Run_Definition_Domain_Model.md) (24 shared connections)
- [Worker Log Event Formatting](Worker_Log_Event_Formatting.md) (20 shared connections)
- [Run State Rendering](Run_State_Rendering.md) (15 shared connections)
- [Event Wire Serialization](Event_Wire_Serialization.md) (10 shared connections)
- [DynamoDB Run Store](DynamoDB_Run_Store.md) (9 shared connections)
- [Run Persistence Orchestration](Run_Persistence_Orchestration.md) (8 shared connections)
- [Reconcile Tick and Report](Reconcile_Tick_and_Report.md) (8 shared connections)
- [Plan and Scope Seam](Plan_and_Scope_Seam.md) (5 shared connections)
- [Result Store Serialization](Result_Store_Serialization.md) (5 shared connections)
- [Event Records Projection](Event_Records_Projection.md) (5 shared connections)
- [Boto3 Adapter Guard](Boto3_Adapter_Guard.md) (4 shared connections)

## Source Files

- `core/DEVELOPMENT.md`
- `core/README.md`
- `core/gherkai_core/adapters/cloud_launcher.py`
- `core/gherkai_core/adapters/fargate_engine.py`
- `core/gherkai_core/adapters/subprocess_engine.py`
- `core/gherkai_core/errors.py`
- `core/gherkai_core/model.py`
- `core/gherkai_core/persist.py`
- `core/gherkai_core/ports.py`
- `core/gherkai_core/reconcile.py`
- `docs/internals/cloud-backend-carriers.md`

## Audit Trail

- EXTRACTED: 269 (89%)
- INFERRED: 34 (11%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*