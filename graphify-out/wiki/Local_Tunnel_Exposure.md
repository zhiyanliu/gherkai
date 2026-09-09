# Local Tunnel Exposure

> 14 nodes · cohesion 0.18

## Key Concepts

- **tunnel.py** (13 connections) — `runtime/gherkai_runtime/tunnel.py`
- **tunnel_host.py** (11 connections) — `runtime/gherkai_runtime/tunnel_host.py`
- **TunnelError** (8 connections) — `runtime/gherkai_runtime/tunnel.py`
- **make_tunnel()** (6 connections) — `runtime/gherkai_runtime/tunnel.py`
- **.start()** (4 connections) — `runtime/gherkai_runtime/tunnel.py`
- **本地应用暴露 / 隧道（--expose-local）** (3 connections) — `CONTEXT.md`
- **_gen_auth()** (3 connections) — `runtime/gherkai_runtime/tunnel.py`
- **test_make_tunnel_unknown_provider()** (2 connections) — `runtime/tests/test_tunnel.py`
- **隧道宿主编排（ADR 0035 决策 3）：起隧道 + 映射 definition、守隧道到 run 终态。 **宿主** = 持有隧道 agent…** (1 connections) — `runtime/gherkai_runtime/tunnel_host.py`
- **Exception** (1 connections)
- **隧道口子（ADR 0035）：把「跑 CLI 的机器可达」的被测应用暴露成云端浏览器可访问的公网 URL。 TunnelProvider 形状 =…** (1 connections) — `runtime/gherkai_runtime/tunnel.py`
- **按 `--tunnel <provider>` 选实现（ADR 0035 决策 1；当前唯一 ngrok，机制先行）。** (1 connections) — `runtime/gherkai_runtime/tunnel.py`
- **隧道起不来 / provider 未知 / 前置缺失——调用方接住归「没开跑就被拒」（退 2）。** (1 connections) — `runtime/gherkai_runtime/tunnel.py`
- **生成隧道专用短命凭据：纯字母数字（规避 URL-encode，ADR 0035 决策 4），每 run 一换。** (1 connections) — `runtime/gherkai_runtime/tunnel.py`

## Relationships

- [Ngrok Tunnel Provider](Ngrok_Tunnel_Provider.md) (6 shared connections)
- [Engine Ports & Adapters](Engine_Ports_%26_Adapters.md) (4 shared connections)
- [Tunnel Host TTL Watchdog](Tunnel_Host_TTL_Watchdog.md) (4 shared connections)
- [Tunnel Setup for Jobs](Tunnel_Setup_for_Jobs.md) (3 shared connections)
- [Tunnel Info Model](Tunnel_Info_Model.md) (2 shared connections)
- [Domain Glossary](Domain_Glossary.md) (1 shared connections)
- [Tunnel Cleanup](Tunnel_Cleanup.md) (1 shared connections)
- [Tunnel Origin URL Mapping](Tunnel_Origin_URL_Mapping.md) (1 shared connections)
- [Resource Naming Source](Resource_Naming_Source.md) (1 shared connections)
- [Composition Root Wiring](Composition_Root_Wiring.md) (1 shared connections)

## Source Files

- `CONTEXT.md`
- `runtime/gherkai_runtime/tunnel.py`
- `runtime/gherkai_runtime/tunnel_host.py`
- `runtime/tests/test_tunnel.py`

## Audit Trail

- EXTRACTED: 38 (95%)
- INFERRED: 2 (5%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*