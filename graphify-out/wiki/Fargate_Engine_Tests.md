# Fargate Engine Tests

> 44 nodes · cohesion 0.12

## Key Concepts

- **test_fargate_engine.py** (76 connections) — `core/tests/test_fargate_engine.py`
- **_engine()** (25 connections) — `core/tests/test_fargate_engine.py`
- **_job()** (23 connections) — `core/tests/test_fargate_engine.py`
- **_put_event()** (12 connections) — `core/tests/test_fargate_engine.py`
- **_stopped_ecs()** (11 connections) — `core/tests/test_fargate_engine.py`
- **_spy_run_task_env()** (9 connections) — `core/tests/test_fargate_engine.py`
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
- **test_run_scope_injects_artifact_s3_env()** (3 connections) — `core/tests/test_fargate_engine.py`
- **test_run_scope_injects_region_never_profile()** (3 connections) — `core/tests/test_fargate_engine.py`
- **test_run_scope_injects_sdk_artifact_dir_env()** (3 connections) — `core/tests/test_fargate_engine.py`
- **test_run_scope_job_in_tagged_for_lifecycle()** (3 connections) — `core/tests/test_fargate_engine.py`
- **test_run_scope_job_key_quotes_scope_id()** (3 connections) — `core/tests/test_fargate_engine.py`
- *... and 19 more nodes in this community*

## Relationships

- [Fargate Event Read Tests](Fargate_Event_Read_Tests.md) (12 shared connections)
- [DynamoDB Event Log](DynamoDB_Event_Log.md) (7 shared connections)
- [Fargate Worker Handle](Fargate_Worker_Handle.md) (7 shared connections)
- [ECS Task Probe Tests](ECS_Task_Probe_Tests.md) (7 shared connections)
- [Run Metadata & S3 Offload](Run_Metadata_%26_S3_Offload.md) (6 shared connections)
- [Fargate Engine Adapter](Fargate_Engine_Adapter.md) (4 shared connections)
- [Core Typed Errors](Core_Typed_Errors.md) (2 shared connections)
- [Event Progress Formatting](Event_Progress_Formatting.md) (2 shared connections)
- [Run State Rendering](Run_State_Rendering.md) (2 shared connections)
- [Event Log & Projection](Event_Log_%26_Projection.md) (1 shared connections)
- [Wire Protocol Serialization](Wire_Protocol_Serialization.md) (1 shared connections)
- [Paginated Final Drain Reads](Paginated_Final_Drain_Reads.md) (1 shared connections)

## Source Files

- `core/tests/test_fargate_engine.py`

## Audit Trail

- EXTRACTED: 165 (99%)
- INFERRED: 1 (1%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*