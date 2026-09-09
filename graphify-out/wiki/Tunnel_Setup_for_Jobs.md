# Tunnel Setup For Jobs

> 7 nodes · cohesion 0.29

## Key Concepts

- **start_tunnel_for_jobs()** (7 connections) — `runtime/gherkai_runtime/tunnel_host.py`
- **TunnelSetup** (4 connections) — `runtime/gherkai_runtime/tunnel_host.py`
- **test_start_tunnel_for_jobs_propagates_tunnel_error()** (4 connections) — `runtime/tests/test_tunnel_host.py`
- **test_start_tunnel_for_jobs_maps_and_injects_headers()** (3 connections) — `runtime/tests/test_tunnel_host.py`
- **隧道就绪后的三件产物：映射过的 definition + 隧道模式的额外请求头 + 隧道事实（收尾凭据）。** (1 connections) — `runtime/gherkai_runtime/tunnel_host.py`
- **起隧道并把 definition 里的 origin 映射成公网 URL（ADR 0035 决策 1/2/4）。 起不来（provider 未知 /…** (1 connections) — `runtime/gherkai_runtime/tunnel_host.py`
- **provider 起不来 → TunnelError 直接冒给调用方（皮归「没开跑就被拒」退 2，不在本层吞成哨兵）。** (1 connections) — `runtime/tests/test_tunnel_host.py`

## Relationships

- [Local Tunnel Exposure](Local_Tunnel_Exposure.md) (3 shared connections)
- [Engine Ports & Adapters](Engine_Ports_%26_Adapters.md) (3 shared connections)
- [Tunnel Host Watchdog](Tunnel_Host_Watchdog.md) (2 shared connections)
- [Job Origin URL Mapping](Job_Origin_URL_Mapping.md) (1 shared connections)

## Source Files

- `runtime/gherkai_runtime/tunnel_host.py`
- `runtime/tests/test_tunnel_host.py`

## Audit Trail

- EXTRACTED: 14 (93%)
- INFERRED: 1 (7%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*