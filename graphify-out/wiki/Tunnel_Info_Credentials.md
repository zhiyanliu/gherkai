# Tunnel Info Credentials

> 6 nodes · cohesion 0.33

## Key Concepts

- **TunnelInfo** (9 connections) — `runtime/gherkai_runtime/tunnel.py`
- **.mapped_base()** (2 connections) — `runtime/gherkai_runtime/tunnel.py`
- **test_mapped_base_embeds_credentials()** (2 connections) — `runtime/tests/test_tunnel.py`
- **test_mapped_base_without_auth_is_plain_url()** (2 connections) — `runtime/tests/test_tunnel.py`
- **一条已建立隧道的事实（可序列化落盘 tunnel.json，供跨进程收尾）。** (1 connections) — `runtime/gherkai_runtime/tunnel.py`
- **替换进 job 文本的形态：凭据内嵌 URL（`https://user:pass@host`，ADR 0035 决策 4 方案①——…** (1 connections) — `runtime/gherkai_runtime/tunnel.py`

## Relationships

- [Tunnel Origin Mapping](Tunnel_Origin_Mapping.md) (3 shared connections)
- [Tunnel Provider Factory](Tunnel_Provider_Factory.md) (2 shared connections)
- [Job Explain & S3 Offload](Job_Explain_%26_S3_Offload.md) (1 shared connections)
- [Submit & Tunnel CLI Tests](Submit_%26_Tunnel_CLI_Tests.md) (1 shared connections)

## Source Files

- `runtime/gherkai_runtime/tunnel.py`
- `runtime/tests/test_tunnel.py`

## Audit Trail

- EXTRACTED: 10 (83%)
- INFERRED: 2 (17%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*