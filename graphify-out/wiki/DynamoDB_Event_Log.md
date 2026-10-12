# DynamoDB Event Log

> 35 nodes · cohesion 0.08

## Key Concepts

- **DdbEventLog** (25 connections) — `core/gherkai_core/adapters/event_log/ddb.py`
- **events_pk()** (15 connections) — `core/gherkai_core/adapters/fargate_engine.py`
- **test_tick_with_ddb_backend()** (10 connections) — `core/tests/test_cloud_reconcile.py`
- **_passed_worker_events()** (8 connections) — `core/tests/test_cloud_reconcile.py`
- **.records()** (7 connections) — `core/gherkai_core/adapters/event_log/ddb.py`
- **_meta()** (6 connections) — `core/tests/test_cloud_reconcile.py`
- **test_ddb_multi_scope_records()** (6 connections) — `core/tests/test_cloud_reconcile.py`
- **test_ddb_records_feed_project()** (6 connections) — `core/tests/test_cloud_reconcile.py`
- **test_ddb_record_exit_independent_keyspace()** (5 connections) — `core/tests/test_cloud_reconcile.py`
- **_put_exit_item()** (5 connections) — `core/tests/test_fargate_engine.py`
- **_put_worker_event()** (4 connections) — `core/tests/test_cloud_reconcile.py`
- **test_ddb_has_exit_single_scope()** (4 connections) — `core/tests/test_cloud_reconcile.py`
- **test_ddb_record_exit_reason_roundtrip()** (4 connections) — `core/tests/test_cloud_reconcile.py`
- **._emit_ts()** (3 connections) — `core/gherkai_core/adapters/event_log/ddb.py`
- **.has_exit()** (3 connections) — `core/gherkai_core/adapters/event_log/ddb.py`
- **.record_exit()** (3 connections) — `core/gherkai_core/adapters/event_log/ddb.py`
- **test_ddb_event_log_queries_with_consistent_read()** (3 connections) — `core/tests/test_cloud_reconcile.py`
- **test_ddb_event_log_reads_worker_events()** (3 connections) — `core/tests/test_cloud_reconcile.py`
- **.__init__()** (2 connections) — `core/gherkai_core/adapters/event_log/ddb.py`
- **test_events_pk_composite_run_id_scope_id()** (2 connections) — `core/tests/test_fargate_engine.py`
- **单个 scope 有没有退出记录（**只读**，退出记录键位确定 → 单 item 点查、不走 records() 重放整 run）。…** (1 connections) — `core/gherkai_core/adapters/event_log/ddb.py`
- **退出观察者 Lambda 调：写 task_exited 到保留高位 SK（独立键空间，机制一）。INSERT 幂等（覆盖同键）。…** (1 connections) — `core/gherkai_core/adapters/event_log/ddb.py`
- **cloud EventLog：从 events 表读全量重放（逐 scope Query）+ 写 task_exited（保留高位 SK）。…** (1 connections) — `core/gherkai_core/adapters/event_log/ddb.py`
- **读某 run 全量 records（逐 scope Query worker 段 events + 取 task_exited）→ 供 project…** (1 connections) — `core/gherkai_core/adapters/event_log/ddb.py`
- **从 events item 还原 worker emit 墙钟（reduce_event 的 now，供算时长）。 写端（worker EventSink）写…** (1 connections) — `core/gherkai_core/adapters/event_log/ddb.py`
- *... and 10 more nodes in this community*

## Relationships

- [Cloud Reconcile Launcher Tests](Cloud_Reconcile_Launcher_Tests.md) (15 shared connections)
- [Fake DDB Table & SQLite Records](Fake_DDB_Table_%26_SQLite_Records.md) (6 shared connections)
- [Fargate Engine Adapter Tests](Fargate_Engine_Adapter_Tests.md) (4 shared connections)
- [Fargate Event Drain Tests](Fargate_Event_Drain_Tests.md) (4 shared connections)
- [Boto3 Guard & Arg Offload](Boto3_Guard_%26_Arg_Offload.md) (3 shared connections)
- [Exit Observer Lambda](Exit_Observer_Lambda.md) (2 shared connections)
- [Cloud Launcher & Fargate Adapters](Cloud_Launcher_%26_Fargate_Adapters.md) (2 shared connections)
- [SQLite Event Log Adapter](SQLite_Event_Log_Adapter.md) (1 shared connections)
- [Lambda Handler Event Parsing Tests](Lambda_Handler_Event_Parsing_Tests.md) (1 shared connections)
- [Job/Scenario Explain Model](Job-Scenario_Explain_Model.md) (1 shared connections)
- [Wire Protocol Serialization](Wire_Protocol_Serialization.md) (1 shared connections)
- [Fargate Task Polling](Fargate_Task_Polling.md) (1 shared connections)

## Source Files

- `core/gherkai_core/adapters/event_log/ddb.py`
- `core/gherkai_core/adapters/fargate_engine.py`
- `core/tests/test_cloud_reconcile.py`
- `core/tests/test_fargate_engine.py`

## Audit Trail

- EXTRACTED: 85 (92%)
- INFERRED: 7 (8%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*