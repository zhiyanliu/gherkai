# Fargate Engine Tests

> 45 nodes · cohesion 0.11

## Key Concepts

- **test_fargate_engine.py** (62 connections) — `core/tests/test_fargate_engine.py`
- **_engine()** (25 connections) — `core/tests/test_fargate_engine.py`
- **_job()** (23 connections) — `core/tests/test_fargate_engine.py`
- **_put_event()** (12 connections) — `core/tests/test_fargate_engine.py`
- **_stopped_ecs()** (10 connections) — `core/tests/test_fargate_engine.py`
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
- *... and 20 more nodes in this community*

## Relationships

- [Engine Ports & Adapters](Engine_Ports_%26_Adapters.md) (9 shared connections)
- [Fargate Worker Handle](Fargate_Worker_Handle.md) (6 shared connections)
- [Exit Code Await Polling](Exit_Code_Await_Polling.md) (6 shared connections)
- [Task Exit Event Records](Task_Exit_Event_Records.md) (4 shared connections)
- [Fargate Engine](Fargate_Engine.md) (3 shared connections)
- [Event Progress Formatting](Event_Progress_Formatting.md) (2 shared connections)
- [Cloud Launcher & DDB Event Log](Cloud_Launcher_%26_DDB_Event_Log.md) (2 shared connections)
- [Worker Exit Code Mapping](Worker_Exit_Code_Mapping.md) (2 shared connections)
- [Delayed ECS Stub](Delayed_ECS_Stub.md) (2 shared connections)
- [Run Result Rendering](Run_Result_Rendering.md) (1 shared connections)
- [Terminal Status Aggregation](Terminal_Status_Aggregation.md) (1 shared connections)
- [State Projection & Planning](State_Projection_%26_Planning.md) (1 shared connections)

## Source Files

- `core/gherkai_core/model.py`
- `core/tests/test_fargate_engine.py`

## Audit Trail

- EXTRACTED: 151 (99%)
- INFERRED: 1 (1%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*