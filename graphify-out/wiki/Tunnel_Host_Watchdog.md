# Tunnel Host Watchdog

> 19 nodes · cohesion 0.15

## Key Concepts

- **test_tunnel_host.py** (17 connections) — `runtime/tests/test_tunnel_host.py`
- **watch_run_and_stop_tunnel()** (8 connections) — `runtime/gherkai_runtime/tunnel_host.py`
- **compute_watch_ttl_s()** (6 connections) — `runtime/gherkai_runtime/tunnel_host.py`
- **_patch_run_store()** (4 connections) — `runtime/tests/test_tunnel_host.py`
- **_state()** (4 connections) — `runtime/tests/test_tunnel_host.py`
- **test_ttl_gives_unbounded_jobs_an_explicit_ceiling()** (4 connections) — `runtime/tests/test_tunnel_host.py`
- **test_ttl_scales_past_the_old_fixed_hour()** (4 connections) — `runtime/tests/test_tunnel_host.py`
- **test_ttl_sums_job_budgets_plus_margin()** (4 connections) — `runtime/tests/test_tunnel_host.py`
- **test_watch_stops_tunnel_on_terminal_state()** (4 connections) — `runtime/tests/test_tunnel_host.py`
- **test_watch_ttl_fallback_when_run_never_settles()** (4 connections) — `runtime/tests/test_tunnel_host.py`
- **test_ttl_empty_definition_is_just_the_margin()** (2 connections) — `runtime/tests/test_tunnel_host.py`
- **按 definition 算 cloud submit 隧道守护的 TTL 秒数 = Σ(各 job 预算) + 启动/级联余量。 **求和而非取…** (1 connections) — `runtime/gherkai_runtime/tunnel_host.py`
- **cloud submit 隧道守护进程的主体（ADR 0035 决策 3 cloud 档）：轮询 DDB run 终态 → 拆隧道； TTL 到点 →…** (1 connections) — `runtime/gherkai_runtime/tunnel_host.py`
- **tunnel_host 单测（ADR 0035 决策 3）：隧道宿主编排——起隧道+映射、TTL 算法、守护循环。…** (1 connections) — `runtime/tests/test_tunnel_host.py`
- **读库一直异常（run 卡死/查询异常）→ 不致命、继续轮询，TTL 到点拆隧道自杀（防 ngrok 泄漏）。** (1 connections) — `runtime/tests/test_tunnel_host.py`
- **Σ(各 job 预算) + 启动余量——求和对任何并发取值都是保守上界（ADR 0034 机制四）。** (1 connections) — `runtime/tests/test_tunnel_host.py`
- **本条锁住被修的病根：12 个默认预算（300s）的 job 已超旧的恒定 1h TTL——TTL 必须随 definition 涨， 否则守护会在 run…** (1 connections) — `runtime/tests/test_tunnel_host.py`
- **`--default-job-timeout <=0`（执行侧不超时）→ job.timeout_s=None：TTL 仍须有限（否则泄漏兜底失效）。** (1 connections) — `runtime/tests/test_tunnel_host.py`
- **把 compose._make_ddb_table 换成吐固定 RunState 序列的 fake（states 用尽后复用最后一个）。** (1 connections) — `runtime/tests/test_tunnel_host.py`

## Relationships

- [Engine Ports & Adapters](Engine_Ports_%26_Adapters.md) (5 shared connections)
- [Local Tunnel Exposure](Local_Tunnel_Exposure.md) (4 shared connections)
- [Boto Guard & S3 Offload](Boto_Guard_%26_S3_Offload.md) (2 shared connections)
- [Tunnel Setup For Jobs](Tunnel_Setup_For_Jobs.md) (2 shared connections)
- [Tunnel Cleanup](Tunnel_Cleanup.md) (1 shared connections)
- [Cloud Target Resolution](Cloud_Target_Resolution.md) (1 shared connections)
- [Cloud Store Composition](Cloud_Store_Composition.md) (1 shared connections)
- [Runtime Naming Source](Runtime_Naming_Source.md) (1 shared connections)
- [SSM Path & Client Composition](SSM_Path_%26_Client_Composition.md) (1 shared connections)
- [Run State Rendering](Run_State_Rendering.md) (1 shared connections)

## Source Files

- `runtime/gherkai_runtime/tunnel_host.py`
- `runtime/tests/test_tunnel_host.py`

## Audit Trail

- EXTRACTED: 43 (98%)
- INFERRED: 1 (2%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*