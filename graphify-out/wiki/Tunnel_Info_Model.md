# Tunnel Info Model

> 6 nodes · cohesion 0.33

## Key Concepts

- **TunnelInfo** (9 connections) — `runtime/gherkai_runtime/tunnel.py`
- **.mapped_base()** (2 connections) — `runtime/gherkai_runtime/tunnel.py`
- **test_mapped_base_embeds_credentials()** (2 connections) — `runtime/tests/test_tunnel.py`
- **test_mapped_base_without_auth_is_plain_url()** (2 connections) — `runtime/tests/test_tunnel.py`
- **一条已建立隧道的事实（可序列化落盘 tunnel.json，供跨进程收尾）。** (1 connections) — `runtime/gherkai_runtime/tunnel.py`
- **替换进 job 文本的形态：凭据内嵌 URL（`https://user:pass@host`，ADR 0035 决策 4 方案①——…** (1 connections) — `runtime/gherkai_runtime/tunnel.py`

## Relationships

- [Ngrok Tunnel Provider](Ngrok_Tunnel_Provider.md) (3 shared connections)
- [Local Tunnel Exposure](Local_Tunnel_Exposure.md) (2 shared connections)
- [Engine Ports & Adapters](Engine_Ports_%26_Adapters.md) (2 shared connections)

## Source Files

- `runtime/gherkai_runtime/tunnel.py`
- `runtime/tests/test_tunnel.py`

## Audit Trail

- EXTRACTED: 10 (83%)
- INFERRED: 2 (17%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*