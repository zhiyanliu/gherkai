# Tunnel Host Orchestration

> 9 nodes · cohesion 0.25

## Key Concepts

- **tunnel_host.py** (11 connections) — `runtime/gherkai_runtime/tunnel_host.py`
- **start_tunnel_for_jobs()** (7 connections) — `runtime/gherkai_runtime/tunnel_host.py`
- **TunnelSetup** (4 connections) — `runtime/gherkai_runtime/tunnel_host.py`
- **test_start_tunnel_for_jobs_propagates_tunnel_error()** (4 connections) — `runtime/tests/test_tunnel_host.py`
- **test_start_tunnel_for_jobs_maps_and_injects_headers()** (3 connections) — `runtime/tests/test_tunnel_host.py`
- **隧道宿主编排（ADR 0035 决策 3）：起隧道 + 映射 definition、守隧道到 run 终态。 **宿主**指持有隧道 agent…** (1 connections) — `runtime/gherkai_runtime/tunnel_host.py`
- **隧道就绪后的三件产物：映射过的 definition + 隧道模式的额外请求头 + 隧道事实（收尾凭据）。** (1 connections) — `runtime/gherkai_runtime/tunnel_host.py`
- **起隧道并把 definition 里的 origin 映射成公网 URL（ADR 0035 决策 1/2/4）。 起不来（provider 未知 /…** (1 connections) — `runtime/gherkai_runtime/tunnel_host.py`
- **provider 起不来 → TunnelError 直接冒给调用方（前端归「没开始执行就被拒」、退出码 2，不在本层吞成哨兵）。** (1 connections) — `runtime/tests/test_tunnel_host.py`

## Relationships

- [Tunnel Watch TTL Daemon](Tunnel_Watch_TTL_Daemon.md) (5 shared connections)
- [Job/Scenario Explain Model](Job-Scenario_Explain_Model.md) (3 shared connections)
- [Cloud Store Composition Root](Cloud_Store_Composition_Root.md) (2 shared connections)
- [Cloud Launcher & Fargate Adapters](Cloud_Launcher_%26_Fargate_Adapters.md) (1 shared connections)
- [Tunnel Port Abstraction](Tunnel_Port_Abstraction.md) (1 shared connections)
- [Core Library Concepts & ADRs](Core_Library_Concepts_%26_ADRs.md) (1 shared connections)
- [Ngrok Tunnel Provider](Ngrok_Tunnel_Provider.md) (1 shared connections)
- [Job Origin Mapping](Job_Origin_Mapping.md) (1 shared connections)

## Source Files

- `runtime/gherkai_runtime/tunnel_host.py`
- `runtime/tests/test_tunnel_host.py`

## Audit Trail

- EXTRACTED: 23 (96%)
- INFERRED: 1 (4%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*