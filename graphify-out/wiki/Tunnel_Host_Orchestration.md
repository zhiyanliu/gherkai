# Tunnel Host Orchestration

> 11 nodes · cohesion 0.20

## Key Concepts

- **gherkai_runtime/__init__.py** (14 connections) — `runtime/gherkai_runtime/__init__.py`
- **tunnel_host.py** (10 connections) — `runtime/gherkai_runtime/tunnel_host.py`
- **start_tunnel_for_jobs()** (7 connections) — `runtime/gherkai_runtime/tunnel_host.py`
- **TunnelSetup** (4 connections) — `runtime/gherkai_runtime/tunnel_host.py`
- **test_start_tunnel_for_jobs_propagates_tunnel_error()** (4 connections) — `runtime/tests/test_tunnel_host.py`
- **test_start_tunnel_for_jobs_maps_and_injects_headers()** (3 connections) — `runtime/tests/test_tunnel_host.py`
- **gherkai：产品本体即组合根共享层（ADR 0016「演进」节）。 持有产品级知识——引擎注册表与装配（compose）、local…** (1 connections) — `runtime/gherkai_runtime/__init__.py`
- **隧道宿主编排（ADR 0035 决策 3）：起隧道 + 映射 definition、守隧道到 run 终态。 **宿主**指持有隧道 agent…** (1 connections) — `runtime/gherkai_runtime/tunnel_host.py`
- **隧道就绪后的三件产物：映射过的 definition + 隧道模式的额外请求头 + 隧道事实（收尾凭据）。** (1 connections) — `runtime/gherkai_runtime/tunnel_host.py`
- **起隧道并把 definition 里的 origin 映射成公网 URL（ADR 0035 决策 1/2/4）。 起不来（provider 未知 /…** (1 connections) — `runtime/gherkai_runtime/tunnel_host.py`
- **provider 起不来 → TunnelError 直接冒给调用方（前端归「没开始执行就被拒」、退出码 2，不在本层吞成哨兵）。** (1 connections) — `runtime/tests/test_tunnel_host.py`

## Relationships

- [Tunnel Host Daemon](Tunnel_Host_Daemon.md) (6 shared connections)
- [Job Domain Models](Job_Domain_Models.md) (4 shared connections)
- [SSM Path Naming](SSM_Path_Naming.md) (2 shared connections)
- [Tunnel Provider](Tunnel_Provider.md) (2 shared connections)
- [CLI Command Handlers](CLI_Command_Handlers.md) (1 shared connections)
- [Test Fixtures and Conftest](Test_Fixtures_and_Conftest.md) (1 shared connections)
- [JSON Contract Guards](JSON_Contract_Guards.md) (1 shared connections)
- [CLI Run Command Tests](CLI_Run_Command_Tests.md) (1 shared connections)
- [Tunnel CLI Wiring](Tunnel_CLI_Wiring.md) (1 shared connections)
- [Local Detached Execution](Local_Detached_Execution.md) (1 shared connections)
- [Cloud Resource Resolution](Cloud_Resource_Resolution.md) (1 shared connections)
- [Resource Naming Source](Resource_Naming_Source.md) (1 shared connections)

## Source Files

- `runtime/gherkai_runtime/__init__.py`
- `runtime/gherkai_runtime/tunnel_host.py`
- `runtime/tests/test_tunnel_host.py`

## Audit Trail

- EXTRACTED: 35 (97%)
- INFERRED: 1 (3%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*