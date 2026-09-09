# Engine Ports & Adapters

> 102 nodes · cohesion 0.05

## Key Concepts

- **Job** (117 connections) — `core/gherkai_core/model.py`
- **model.py** (77 connections) — `core/gherkai_core/model.py`
- **Scenario** (62 connections) — `core/gherkai_core/model.py`
- **Step** (62 connections) — `core/gherkai_core/model.py`
- **wire.py** (37 connections) — `core/gherkai_core/wire.py`
- **core/DEVELOPMENT.md** (27 connections) — `core/DEVELOPMENT.md`
- **StepArgument** (24 connections) — `core/gherkai_core/model.py`
- **fargate_engine.py** (23 connections) — `core/gherkai_core/adapters/fargate_engine.py`
- **test_arg_offload.py** (23 connections) — `core/tests/test_arg_offload.py`
- **scope.py** (21 connections) — `core/gherkai_core/scope.py`
- **subprocess_engine.py** (18 connections) — `core/gherkai_core/adapters/subprocess_engine.py`
- **parse.py** (15 connections) — `core/gherkai_core/parse.py`
- **event_from_line()** (15 connections) — `core/gherkai_core/wire.py`
- **_FakeEcs** (15 connections) — `core/tests/test_fargate_engine.py`
- **_SeqEcs** (15 connections) — `core/tests/test_fargate_engine.py`
- **_FakeSchedulerClient** (15 connections) — `deploy_aws/tests/test_lambda_handlers.py`
- **_timeout_built()** (15 connections) — `deploy_aws/tests/test_lambda_handlers.py`
- **PlanError** (14 connections) — `core/gherkai_core/errors.py`
- **parse_feature()** (14 connections) — `core/gherkai_core/parse.py`
- **_FakeProc** (14 connections) — `runtime/tests/test_tunnel.py`
- **ParsedScenario** (13 connections) — `core/gherkai_core/parse.py`
- **test_offload_unblocks_oversized_docstring_real()** (12 connections) — `core/tests/test_cloud_integration.py`
- **errors.py** (11 connections) — `core/gherkai_core/errors.py`
- **test_offload_round_trip_real()** (11 connections) — `core/tests/test_cloud_integration.py`
- **ConflictException** (10 connections) — `deploy_aws/tests/test_lambda_handlers.py`
- *... and 77 more nodes in this community*

## Relationships

- [Run State Rendering & Boto Guard](Run_State_Rendering_%26_Boto_Guard.md) (43 shared connections)
- [Run Result Verdict Model](Run_Result_Verdict_Model.md) (42 shared connections)
- [DynamoDB RunStore Conditional Writes](DynamoDB_RunStore_Conditional_Writes.md) (39 shared connections)
- [SQLite Event Log & Projection](SQLite_Event_Log_%26_Projection.md) (24 shared connections)
- [Cloud Launcher & DDB EventLog](Cloud_Launcher_%26_DDB_EventLog.md) (21 shared connections)
- [Event Formatting & Cost Model](Event_Formatting_%26_Cost_Model.md) (20 shared connections)
- [Reconcile Ports & Tick](Reconcile_Ports_%26_Tick.md) (16 shared connections)
- [Wire Protocol Serialization](Wire_Protocol_Serialization.md) (16 shared connections)
- [Feature Planning to Jobs](Feature_Planning_to_Jobs.md) (15 shared connections)
- [Terminal Status Aggregation](Terminal_Status_Aggregation.md) (14 shared connections)
- [ResultStore Local/S3](ResultStore_Local-S3.md) (13 shared connections)
- [Render & ReportStore Local](Render_%26_ReportStore_Local.md) (13 shared connections)

## Source Files

- `CONTEXT.md`
- `core/DEVELOPMENT.md`
- `core/gherkai_core/adapters/cloud_launcher.py`
- `core/gherkai_core/adapters/fargate_engine.py`
- `core/gherkai_core/adapters/subprocess_engine.py`
- `core/gherkai_core/errors.py`
- `core/gherkai_core/model.py`
- `core/gherkai_core/parse.py`
- `core/gherkai_core/scope.py`
- `core/gherkai_core/wire.py`
- `core/tests/README.md`
- `core/tests/test_arg_offload.py`
- `core/tests/test_cloud_integration.py`
- `core/tests/test_ddb_run_store.py`
- `core/tests/test_fargate_engine.py`
- `core/tests/test_project.py`
- `core/tests/test_reconcile.py`
- `core/tests/test_sqlite_event_log.py`
- `core/tests/test_wire.py`
- `deploy_aws/tests/test_lambda_handlers.py`

## Audit Trail

- EXTRACTED: 556 (82%)
- INFERRED: 120 (18%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*