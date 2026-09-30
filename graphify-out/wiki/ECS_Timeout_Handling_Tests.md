# ECS Timeout Handling Tests

> 20 nodes · cohesion 0.10

## Key Concepts

- **_FakeEcs** (25 connections) — `deploy_aws/tests/test_lambda_handlers.py`
- **test_handle_timeout_converges_directly_when_task_gone()** (4 connections) — `deploy_aws/tests/test_lambda_handlers.py`
- **test_handle_timeout_converges_from_describe_keeps_timeout_attribution_of_own_stop()** (4 connections) — `deploy_aws/tests/test_lambda_handlers.py`
- **test_handle_timeout_converges_from_describe_when_task_already_stopped()** (4 connections) — `deploy_aws/tests/test_lambda_handlers.py`
- **test_handle_timeout_leaves_a_stopping_task_to_the_observer()** (4 connections) — `deploy_aws/tests/test_lambda_handlers.py`
- **test_handle_timeout_noop_when_exit_in_flight()** (4 connections) — `deploy_aws/tests/test_lambda_handlers.py`
- **test_handle_timeout_noop_when_job_terminal()** (4 connections) — `deploy_aws/tests/test_lambda_handlers.py`
- **test_handle_timeout_stops_matching_task()** (4 connections) — `deploy_aws/tests/test_lambda_handlers.py`
- **.describe_tasks()** (1 connections) — `deploy_aws/tests/test_lambda_handlers.py`
- **.__init__()** (1 connections) — `deploy_aws/tests/test_lambda_handlers.py`
- **.list_tasks()** (1 connections) — `deploy_aws/tests/test_lambda_handlers.py`
- **.stop_task()** (1 connections) — `deploy_aws/tests/test_lambda_handlers.py`
- **list_tasks/describe_tasks/stop_task 记录器。`task_arns` 是运行中的 task；`tasks` 是带状态的…** (1 connections) — `deploy_aws/tests/test_lambda_handlers.py`
- **仍 running + task 运行中 → StopTask(reason 含哨兵) → 让 STOPPED→exit_observer…** (1 connections) — `deploy_aws/tests/test_lambda_handlers.py`
- **到点时 job 已终态（正常运行结束）→ 幂等 no-op（不碰 ECS——schedule 到点即删，双方零残留）。** (1 connections) — `deploy_aws/tests/test_lambda_handlers.py`
- **退出记录已在（投影在途）→ 不动手，让既有链收敛（不覆盖真退出记录——被拒方案护栏）。** (1 connections) — `deploy_aws/tests/test_lambda_handlers.py`
- **task 无踪且无退出记录（STOPPED 事件丢投等）→ 直接 record_exit(timed_out=True) 收敛 （对位 local…** (1 connections) — `deploy_aws/tests/test_lambda_handlers.py`
- **task 正在停止（desiredStatus=STOPPED、lastStatus 未到 STOPPED）→ 不在 RUNNING…** (1 connections) — `deploy_aws/tests/test_lambda_handlers.py`
- **task 已 STOPPED 却无退出记录（STOPPED 事件丢投）→ 用与观察者同一提取函数从 DescribeTasks 落**真**退出记录…** (1 connections) — `deploy_aws/tests/test_lambda_handlers.py`
- **上一轮已 StopTask（stoppedReason 带哨兵）、事件丢投、本轮再扫到它已 STOPPED → 落记录仍归因 timeout。** (1 connections) — `deploy_aws/tests/test_lambda_handlers.py`

## Relationships

- [Job Domain Models](Job_Domain_Models.md) (12 shared connections)
- [Lambda Handler Tests](Lambda_Handler_Tests.md) (8 shared connections)
- [Task List Pagination](Task_List_Pagination.md) (2 shared connections)
- [Cloud Store Adapters](Cloud_Store_Adapters.md) (1 shared connections)
- [Run State Store](Run_State_Store.md) (1 shared connections)
- [Run Result Aggregation Tree](Run_Result_Aggregation_Tree.md) (1 shared connections)
- [Boto Guard and Arg Offload](Boto_Guard_and_Arg_Offload.md) (1 shared connections)
- [SSM Path Naming](SSM_Path_Naming.md) (1 shared connections)

## Source Files

- `deploy_aws/tests/test_lambda_handlers.py`

## Audit Trail

- EXTRACTED: 36 (78%)
- INFERRED: 10 (22%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*