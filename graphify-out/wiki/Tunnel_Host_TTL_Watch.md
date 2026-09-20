# Tunnel Host TTL Watch

> 21 nodes · cohesion 0.13

## Key Concepts

- **test_tunnel_host.py** (18 connections) — `runtime/tests/test_tunnel_host.py`
- **watch_run_and_stop_tunnel()** (9 connections) — `runtime/gherkai_runtime/tunnel_host.py`
- **compute_watch_ttl_s()** (6 connections) — `runtime/gherkai_runtime/tunnel_host.py`
- **_patch_run_store()** (4 connections) — `runtime/tests/test_tunnel_host.py`
- **_state()** (4 connections) — `runtime/tests/test_tunnel_host.py`
- **test_ttl_gives_unbounded_jobs_an_explicit_ceiling()** (4 connections) — `runtime/tests/test_tunnel_host.py`
- **test_ttl_scales_past_the_old_fixed_hour()** (4 connections) — `runtime/tests/test_tunnel_host.py`
- **test_ttl_sums_job_budgets_plus_margin()** (4 connections) — `runtime/tests/test_tunnel_host.py`
- **test_watch_stops_tunnel_on_terminal_state()** (4 connections) — `runtime/tests/test_tunnel_host.py`
- **test_watch_ttl_fallback_when_run_never_settles()** (4 connections) — `runtime/tests/test_tunnel_host.py`
- **test_watch_stops_tunnel_even_when_store_assembly_fails()** (3 connections) — `runtime/tests/test_tunnel_host.py`
- **test_ttl_empty_definition_is_just_the_margin()** (2 connections) — `runtime/tests/test_tunnel_host.py`
- **按 definition 算 cloud submit 隧道守护的 TTL 秒数为 Σ(各 job 预算) + 启动/级联余量。 **求和而非取…** (1 connections) — `runtime/gherkai_runtime/tunnel_host.py`
- **cloud submit 隧道守护进程的主体（ADR 0035 决策 3 云端后端）：轮询 DDB run 终态 → 拆隧道； TTL 到点 →…** (1 connections) — `runtime/gherkai_runtime/tunnel_host.py`
- **tunnel_host 单测（ADR 0035 决策 3）：隧道宿主编排——起隧道+映射、TTL 算法、守护循环。…** (1 connections) — `runtime/tests/test_tunnel_host.py`
- **读库一直异常（run 卡死/查询异常）→ 不致命、继续轮询，TTL 到点拆隧道自杀（防 ngrok 泄漏）。** (1 connections) — `runtime/tests/test_tunnel_host.py`
- **store 装配段抛（region 解析不出/凭证坏）→ 守护进程带着异常退出，但隧道**必须已拆**（ADR 0035：守护进程是隧道…** (1 connections) — `runtime/tests/test_tunnel_host.py`
- **Σ(各 job 预算) + 启动余量——求和对任何并发取值都是保守上界（ADR 0034 机制四）。** (1 connections) — `runtime/tests/test_tunnel_host.py`
- **本条锁住被修的病根：12 个默认预算（300s）的 job 已超旧的恒定 1h TTL——TTL 必须随 definition 涨， 否则守护会在 run…** (1 connections) — `runtime/tests/test_tunnel_host.py`
- **`--default-job-timeout <=0`（执行侧不超时）→ job.timeout_s=None：TTL 仍须有限（否则泄漏兜底失效）。** (1 connections) — `runtime/tests/test_tunnel_host.py`
- **把 compose._make_ddb_table 换成吐固定 RunState 序列的 fake（states 用尽后复用最后一个）。** (1 connections) — `runtime/tests/test_tunnel_host.py`

## Relationships

- [Tunnel Host Orchestration](Tunnel_Host_Orchestration.md) (5 shared connections)
- [Run Metadata & S3 Offload](Run_Metadata_%26_S3_Offload.md) (5 shared connections)
- [Run State Rendering](Run_State_Rendering.md) (3 shared connections)
- [Tunnel Provider](Tunnel_Provider.md) (2 shared connections)
- [SSM Paths & Composition Root](SSM_Paths_%26_Composition_Root.md) (2 shared connections)
- [Worker Locator & AWS Resolution](Worker_Locator_%26_AWS_Resolution.md) (1 shared connections)
- [CLI Test Fixtures](CLI_Test_Fixtures.md) (1 shared connections)

## Source Files

- `runtime/gherkai_runtime/tunnel_host.py`
- `runtime/tests/test_tunnel_host.py`

## Audit Trail

- EXTRACTED: 46 (98%)
- INFERRED: 1 (2%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*