# DynamoDB Event Log

> 40 nodes · cohesion 0.09

## Key Concepts

- **test_cloud_reconcile.py** (38 connections) — `core/tests/test_cloud_reconcile.py`
- **DdbEventLog** (25 connections) — `core/gherkai_core/adapters/event_log/ddb.py`
- **fargate_engine.py** (17 connections) — `core/gherkai_core/adapters/fargate_engine.py`
- **events_pk()** (15 connections) — `core/gherkai_core/adapters/fargate_engine.py`
- **event_log/ddb.py** (12 connections) — `core/gherkai_core/adapters/event_log/ddb.py`
- **event_log/__init__.py** (11 connections) — `core/gherkai_core/adapters/event_log/__init__.py`
- **test_tick_with_ddb_backend()** (10 connections) — `core/tests/test_cloud_reconcile.py`
- **_passed_worker_events()** (8 connections) — `core/tests/test_cloud_reconcile.py`
- **.records()** (7 connections) — `core/gherkai_core/adapters/event_log/ddb.py`
- **_meta()** (6 connections) — `core/tests/test_cloud_reconcile.py`
- **test_ddb_multi_scope_records()** (6 connections) — `core/tests/test_cloud_reconcile.py`
- **test_ddb_records_feed_project()** (6 connections) — `core/tests/test_cloud_reconcile.py`
- **test_ddb_record_exit_independent_keyspace()** (5 connections) — `core/tests/test_cloud_reconcile.py`
- **_put_worker_event()** (4 connections) — `core/tests/test_cloud_reconcile.py`
- **test_ddb_has_exit_single_scope()** (4 connections) — `core/tests/test_cloud_reconcile.py`
- **test_ddb_record_exit_reason_roundtrip()** (4 connections) — `core/tests/test_cloud_reconcile.py`
- **._emit_ts()** (3 connections) — `core/gherkai_core/adapters/event_log/ddb.py`
- **.has_exit()** (3 connections) — `core/gherkai_core/adapters/event_log/ddb.py`
- **.record_exit()** (3 connections) — `core/gherkai_core/adapters/event_log/ddb.py`
- **test_ddb_event_log_queries_with_consistent_read()** (3 connections) — `core/tests/test_cloud_reconcile.py`
- **test_ddb_event_log_reads_worker_events()** (3 connections) — `core/tests/test_cloud_reconcile.py`
- **test_events_pk_composite_run_id_scope_id()** (2 connections) — `core/tests/test_fargate_engine.py`
- **DdbEventLog（ADR 0034 cloud 侧）：cloud 无状态批量运行的 EventLog——从 DDB events 表读全量重放 + 写…** (1 connections) — `core/gherkai_core/adapters/event_log/ddb.py`
- **单个 scope 有没有退出记录（**只读**，退出记录键位确定 → 单 item 点查、不走 records() 重放整 run）。…** (1 connections) — `core/gherkai_core/adapters/event_log/ddb.py`
- **退出观察者 Lambda 调：写 task_exited 到保留高位 SK（独立键空间，机制一）。INSERT 幂等（覆盖同键）。…** (1 connections) — `core/gherkai_core/adapters/event_log/ddb.py`
- *... and 15 more nodes in this community*

## Relationships

- [Event Log & Projection](Event_Log_%26_Projection.md) (12 shared connections)
- [Run Metadata & S3 Offload](Run_Metadata_%26_S3_Offload.md) (10 shared connections)
- [Cloud Launcher](Cloud_Launcher.md) (10 shared connections)
- [Fargate Engine Tests](Fargate_Engine_Tests.md) (7 shared connections)
- [Run State Rendering](Run_State_Rendering.md) (7 shared connections)
- [Fargate Engine Adapter](Fargate_Engine_Adapter.md) (6 shared connections)
- [AWS Adapter Clients](AWS_Adapter_Clients.md) (3 shared connections)
- [Event Progress Formatting](Event_Progress_Formatting.md) (3 shared connections)
- [Reconcile Orchestration](Reconcile_Orchestration.md) (3 shared connections)
- [Boto Guard & Arg Offload](Boto_Guard_%26_Arg_Offload.md) (2 shared connections)
- [SQLite Event Log](SQLite_Event_Log.md) (2 shared connections)
- [Wire Protocol Serialization](Wire_Protocol_Serialization.md) (2 shared connections)

## Source Files

- `core/gherkai_core/adapters/event_log/__init__.py`
- `core/gherkai_core/adapters/event_log/ddb.py`
- `core/gherkai_core/adapters/fargate_engine.py`
- `core/tests/test_cloud_reconcile.py`
- `core/tests/test_fargate_engine.py`

## Audit Trail

- EXTRACTED: 137 (95%)
- INFERRED: 7 (5%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*