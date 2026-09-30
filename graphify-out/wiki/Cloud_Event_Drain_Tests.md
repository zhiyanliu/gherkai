# Cloud Event Drain Tests

> 35 nodes · cohesion 0.11

## Key Concepts

- **_engine()** (25 connections) — `core/tests/test_fargate_engine.py`
- **_job()** (23 connections) — `core/tests/test_fargate_engine.py`
- **_put_event()** (12 connections) — `core/tests/test_fargate_engine.py`
- **_stopped_ecs()** (11 connections) — `core/tests/test_fargate_engine.py`
- **test_read_events_ignores_exit_item_alongside_worker_events()** (8 connections) — `core/tests/test_fargate_engine.py`
- **test_read_events_ignores_exit_item_on_stopped_drain_path()** (6 connections) — `core/tests/test_fargate_engine.py`
- **test_read_events_only_this_scope_not_other()** (6 connections) — `core/tests/test_fargate_engine.py`
- **test_read_events_scope_done_then_network_exit_raises_network_error()** (6 connections) — `core/tests/test_fargate_engine.py`
- **test_read_events_scope_done_then_nonzero_exit_raises()** (6 connections) — `core/tests/test_fargate_engine.py`
- **test_read_events_scope_done_waits_for_stopped_before_reading_exit()** (6 connections) — `core/tests/test_fargate_engine.py`
- **_put_exit_item()** (5 connections) — `core/tests/test_fargate_engine.py`
- **test_read_events_incremental_across_polls()** (5 connections) — `core/tests/test_fargate_engine.py`
- **test_read_events_stopped_clean_exit_zero_terminates_without_raise()** (5 connections) — `core/tests/test_fargate_engine.py`
- **test_read_events_stopped_without_scope_done_drains_then_raises()** (5 connections) — `core/tests/test_fargate_engine.py`
- **test_read_events_yields_in_seq_order_until_scope_done()** (5 connections) — `core/tests/test_fargate_engine.py`
- **test_read_events_midscene_lowlevel_marshalling_and_ascending_read()** (4 connections) — `core/tests/test_fargate_engine.py`
- **test_run_scope_runtask_failure_raises_meaningful_error()** (4 connections) — `core/tests/test_fargate_engine.py`
- **test_handle_stop_calls_stop_task()** (3 connections) — `core/tests/test_fargate_engine.py`
- **test_run_scope_job_in_tagged_for_lifecycle()** (3 connections) — `core/tests/test_fargate_engine.py`
- **test_run_scope_job_key_quotes_scope_id()** (3 connections) — `core/tests/test_fargate_engine.py`
- **test_run_scope_puts_job_to_s3()** (3 connections) — `core/tests/test_fargate_engine.py`
- **test_run_scope_runtask_injects_env()** (3 connections) — `core/tests/test_fargate_engine.py`
- **test_runtask_sets_started_by_run_id()** (3 connections) — `core/tests/test_fargate_engine.py`
- **.scope_id()** (2 connections) — `core/gherkai_core/model.py`
- **worker 崩溃没发 scope_done：迭代器读完已落事件 → 见 STOPPED → 强一致 drain 补末尾 → raise 非零退出。** (1 connections) — `core/tests/test_fargate_engine.py`
- *... and 10 more nodes in this community*

## Relationships

- [Fargate Engine Tests](Fargate_Engine_Tests.md) (29 shared connections)
- [Job Domain Models](Job_Domain_Models.md) (3 shared connections)
- [DynamoDB Event Log](DynamoDB_Event_Log.md) (2 shared connections)
- [Run Result Aggregation Tree](Run_Result_Aggregation_Tree.md) (1 shared connections)
- [Fargate Engine Adapter](Fargate_Engine_Adapter.md) (1 shared connections)
- [Cloud Reconcile Tests](Cloud_Reconcile_Tests.md) (1 shared connections)
- [Event Gap & ECS Polling](Event_Gap_%26_ECS_Polling.md) (1 shared connections)
- [Event Sequence Gap Handling](Event_Sequence_Gap_Handling.md) (1 shared connections)

## Source Files

- `core/gherkai_core/model.py`
- `core/tests/test_fargate_engine.py`

## Audit Trail

- EXTRACTED: 105 (99%)
- INFERRED: 1 (1%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*