# Cloud Launcher

> 21 nodes · cohesion 0.14

## Key Concepts

- **CloudLauncher** (17 connections) — `core/gherkai_core/adapters/cloud_launcher.py`
- **_RecorderWatch** (15 connections) — `core/tests/test_cloud_reconcile.py`
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
- **CloudLauncher.launch → resolver 选 engine → start_scope（fire-and-forget，不轮询）。** (1 connections) — `core/tests/test_cloud_reconcile.py`
- **job.timeout_s 非 None → launch 后 arm(run_id, scope_id, timeout_s)（ADR 0034「job…** (1 connections) — `core/tests/test_cloud_reconcile.py`
- **无预算（timeout_s=None）→ 不建 schedule（idle 零成本：不为不超时的 job 造任何云资源）。** (1 connections) — `core/tests/test_cloud_reconcile.py`
- **武装先于起 task（ADR 0034「job timeout」节 best-effort 边界）：launch 与其失败补偿双失败时， 先建的…** (1 connections) — `core/tests/test_cloud_reconcile.py`
- **start_scope 抛异常：arm 已先行（schedule 在，双失败兜底生效）、异常照常冒泡（tick 靠它触发 launch 失败补偿…** (1 connections) — `core/tests/test_cloud_reconcile.py`
- **武装失败 best-effort（ADR 0034「job timeout」节边界）：不抛、task 已起——降级 tick 防御扫。** (1 connections) — `core/tests/test_cloud_reconcile.py`
- **.arm()** (1 connections) — `core/tests/test_cloud_reconcile.py`
- **.__init__()** (1 connections) — `core/tests/test_cloud_reconcile.py`

## Relationships

- [Job Domain Models](Job_Domain_Models.md) (13 shared connections)
- [Cloud Reconcile Tests](Cloud_Reconcile_Tests.md) (11 shared connections)
- [EventBridge Timeout Watch](EventBridge_Timeout_Watch.md) (1 shared connections)
- [Reconciler Lambda](Reconciler_Lambda.md) (1 shared connections)
- [Cloud Store Adapters](Cloud_Store_Adapters.md) (1 shared connections)
- [Run State Store](Run_State_Store.md) (1 shared connections)
- [Run Result Aggregation Tree](Run_Result_Aggregation_Tree.md) (1 shared connections)
- [Run Scheduling Core](Run_Scheduling_Core.md) (1 shared connections)

## Source Files

- `core/gherkai_core/adapters/cloud_launcher.py`
- `core/tests/test_cloud_reconcile.py`

## Audit Trail

- EXTRACTED: 46 (78%)
- INFERRED: 13 (22%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*