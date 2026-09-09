# Engine Ports & Adapters

> 96 nodes · cohesion 0.05

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
- **exceptions** (10 connections) — `deploy_aws/tests/test_lambda_handlers.py`
- **test_meta_json_holds_pointers_not_payload()** (9 connections) — `core/tests/test_arg_offload.py`
- **test_reader_without_offloader_fails_loud_on_offloaded_meta()** (9 connections) — `core/tests/test_arg_offload.py`
- *... and 71 more nodes in this community*

## Relationships

- [Run Result Rendering](Run_Result_Rendering.md) (65 shared connections)
- [Run State Rendering](Run_State_Rendering.md) (56 shared connections)
- [Event Progress Formatting](Event_Progress_Formatting.md) (33 shared connections)
- [SQLite Event Log](SQLite_Event_Log.md) (23 shared connections)
- [Feature Planning](Feature_Planning.md) (22 shared connections)
- [S3 Result Store](S3_Result_Store.md) (18 shared connections)
- [Cloud Launcher & DDB Event Log](Cloud_Launcher_%26_DDB_Event_Log.md) (16 shared connections)
- [Boto Guard & S3 Offload](Boto_Guard_%26_S3_Offload.md) (15 shared connections)
- [Terminal Status Aggregation](Terminal_Status_Aggregation.md) (12 shared connections)
- [Run Scheduling Engine](Run_Scheduling_Engine.md) (11 shared connections)
- [Architecture Decision Records](Architecture_Decision_Records.md) (10 shared connections)
- [Job JSON Serialization](Job_JSON_Serialization.md) (10 shared connections)

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
- `core/tests/test_project.py`
- `core/tests/test_reconcile.py`
- `core/tests/test_sqlite_event_log.py`
- `core/tests/test_wire.py`
- `deploy_aws/tests/test_lambda_handlers.py`
- `runtime/tests/test_tunnel.py`

## Audit Trail

- EXTRACTED: 546 (84%)
- INFERRED: 106 (16%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*