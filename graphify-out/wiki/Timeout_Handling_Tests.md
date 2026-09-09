# Timeout Handling Tests

> 14 nodes · cohesion 0.14

## Key Concepts

- **_FakeEcs** (18 connections) — `deploy_aws/tests/test_lambda_handlers.py`
- **test_handle_timeout_converges_directly_when_task_gone()** (4 connections) — `deploy_aws/tests/test_lambda_handlers.py`
- **test_handle_timeout_noop_when_exit_in_flight()** (4 connections) — `deploy_aws/tests/test_lambda_handlers.py`
- **test_handle_timeout_noop_when_job_terminal()** (4 connections) — `deploy_aws/tests/test_lambda_handlers.py`
- **test_handle_timeout_stops_matching_task()** (4 connections) — `deploy_aws/tests/test_lambda_handlers.py`
- **.describe_tasks()** (1 connections) — `deploy_aws/tests/test_lambda_handlers.py`
- **.__init__()** (1 connections) — `deploy_aws/tests/test_lambda_handlers.py`
- **.list_tasks()** (1 connections) — `deploy_aws/tests/test_lambda_handlers.py`
- **.stop_task()** (1 connections) — `deploy_aws/tests/test_lambda_handlers.py`
- **list_tasks/describe_tasks/stop_task 记录器（describe 返回带 SCOPE_ID env 的 overrides）。** (1 connections) — `deploy_aws/tests/test_lambda_handlers.py`
- **仍 running + task 在跑 → StopTask(reason 含哨兵) → 让 STOPPED→exit_observer…** (1 connections) — `deploy_aws/tests/test_lambda_handlers.py`
- **到点时 job 已终态（正常跑完）→ 幂等 no-op（不碰 ECS——schedule 到点即删，双方零残留）。** (1 connections) — `deploy_aws/tests/test_lambda_handlers.py`
- **退出记录已在（投影在途）→ 不动手，让既有链收敛（不覆盖真退出记录——被拒方案护栏）。** (1 connections) — `deploy_aws/tests/test_lambda_handlers.py`
- **task 无踪且无退出记录（STOPPED 事件丢投等）→ 直接 record_exit(timed_out=True) 收敛 （对位 local…** (1 connections) — `deploy_aws/tests/test_lambda_handlers.py`

## Relationships

- [Engine Ports & Adapters](Engine_Ports_%26_Adapters.md) (7 shared connections)
- [Lambda Handler Tests](Lambda_Handler_Tests.md) (5 shared connections)
- [Run State Rendering](Run_State_Rendering.md) (2 shared connections)
- [Run Result Rendering](Run_Result_Rendering.md) (1 shared connections)
- [Boto Guard & S3 Offload](Boto_Guard_%26_S3_Offload.md) (1 shared connections)
- [SSM Path & Client Composition](SSM_Path_%26_Client_Composition.md) (1 shared connections)

## Source Files

- `deploy_aws/tests/test_lambda_handlers.py`

## Audit Trail

- EXTRACTED: 22 (73%)
- INFERRED: 8 (27%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*