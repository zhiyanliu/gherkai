# Cloud Reconcile Launcher Tests

> 26 nodes · cohesion 0.14

## Key Concepts

- **test_cloud_reconcile.py** (38 connections) — `core/tests/test_cloud_reconcile.py`
- **CloudLauncher** (17 connections) — `core/gherkai_core/adapters/cloud_launcher.py`
- **_RecorderWatch** (15 connections) — `core/tests/test_cloud_reconcile.py`
- **_FakeStartEngine** (14 connections) — `core/tests/test_cloud_reconcile.py`
- **_job()** (11 connections) — `core/tests/test_cloud_reconcile.py`
- **test_cloud_launcher_arm_failure_does_not_block_launch()** (6 connections) — `core/tests/test_cloud_reconcile.py`
- **test_cloud_launcher_arms_timeout_watch()** (6 connections) — `core/tests/test_cloud_reconcile.py`
- **test_cloud_launcher_no_arm_without_timeout()** (6 connections) — `core/tests/test_cloud_reconcile.py`
- **test_cloud_launcher_calls_start_scope()** (5 connections) — `core/tests/test_cloud_reconcile.py`
- **test_cloud_launcher_launch_failure_still_armed_and_raises()** (5 connections) — `core/tests/test_cloud_reconcile.py`
- **test_cloud_launcher_arms_before_start_scope()** (4 connections) — `core/tests/test_cloud_reconcile.py`
- **.launch()** (2 connections) — `core/gherkai_core/adapters/cloud_launcher.py`
- **.__init__()** (1 connections) — `core/gherkai_core/adapters/cloud_launcher.py`
- **Job** (1 connections)
- **cloud Launcher：按 job.engine 选 FargateEngine（经注入的…** (1 connections) — `core/gherkai_core/adapters/cloud_launcher.py`
- **.__init__()** (1 connections) — `core/tests/test_cloud_reconcile.py`
- **.start_scope()** (1 connections) — `core/tests/test_cloud_reconcile.py`
- **cloud 无状态批量运行 core 侧测试（ADR 0034 云端后端）：DdbEventLog + CloudLauncher +…** (1 connections) — `core/tests/test_cloud_reconcile.py`
- **CloudLauncher.launch → resolver 选 engine → start_scope（fire-and-forget，不轮询）。** (1 connections) — `core/tests/test_cloud_reconcile.py`
- **job.timeout_s 非 None → launch 后 arm(run_id, scope_id, timeout_s)（ADR 0034「job…** (1 connections) — `core/tests/test_cloud_reconcile.py`
- **无预算（timeout_s=None）→ 不建 schedule（idle 零成本：不为不超时的 job 造任何云资源）。** (1 connections) — `core/tests/test_cloud_reconcile.py`
- **武装先于起 task（ADR 0034「job timeout」节 best-effort 边界）：launch 与其失败补偿双失败时， 先建的…** (1 connections) — `core/tests/test_cloud_reconcile.py`
- **start_scope 抛异常：arm 已先行（schedule 在，双失败兜底生效）、异常照常冒泡（tick 靠它触发 launch 失败补偿…** (1 connections) — `core/tests/test_cloud_reconcile.py`
- **武装失败 best-effort（ADR 0034「job timeout」节边界）：不抛、task 已起——降级 tick 防御扫。** (1 connections) — `core/tests/test_cloud_reconcile.py`
- **.arm()** (1 connections) — `core/tests/test_cloud_reconcile.py`
- *... and 1 more nodes in this community*

## Relationships

- [DynamoDB Event Log](DynamoDB_Event_Log.md) (15 shared connections)
- [Job/Scenario Explain Model](Job-Scenario_Explain_Model.md) (13 shared connections)
- [Cloud Launcher & Fargate Adapters](Cloud_Launcher_%26_Fargate_Adapters.md) (10 shared connections)
- [Job State Serialization](Job_State_Serialization.md) (3 shared connections)
- [Run State Rendering & DDB Store](Run_State_Rendering_%26_DDB_Store.md) (3 shared connections)
- [Exit Observer Lambda](Exit_Observer_Lambda.md) (2 shared connections)
- [Fake DDB Table & SQLite Records](Fake_DDB_Table_%26_SQLite_Records.md) (1 shared connections)
- [Reconcile Tick & Report Finalize](Reconcile_Tick_%26_Report_Finalize.md) (1 shared connections)
- [SQLite Event Log Adapter](SQLite_Event_Log_Adapter.md) (1 shared connections)
- [Test Fixtures & Conftest](Test_Fixtures_%26_Conftest.md) (1 shared connections)
- [Schedule Module Tests](Schedule_Module_Tests.md) (1 shared connections)

## Source Files

- `core/gherkai_core/adapters/cloud_launcher.py`
- `core/tests/test_cloud_reconcile.py`

## Audit Trail

- EXTRACTED: 77 (79%)
- INFERRED: 20 (21%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*