# Tunnel Port Abstraction

> 14 nodes · cohesion 0.16

## Key Concepts

- **tunnel.py** (14 connections) — `runtime/gherkai_runtime/tunnel.py`
- **TunnelInfo** (9 connections) — `runtime/gherkai_runtime/tunnel.py`
- **TunnelError** (8 connections) — `runtime/gherkai_runtime/tunnel.py`
- **.start()** (5 connections) — `runtime/gherkai_runtime/tunnel.py`
- **_gen_auth()** (3 connections) — `runtime/gherkai_runtime/tunnel.py`
- **.mapped_base()** (2 connections) — `runtime/gherkai_runtime/tunnel.py`
- **test_mapped_base_embeds_credentials()** (2 connections) — `runtime/tests/test_tunnel.py`
- **test_mapped_base_without_auth_is_plain_url()** (2 connections) — `runtime/tests/test_tunnel.py`
- **Exception** (1 connections)
- **隧道口子（ADR 0035）：把 CLI 所在机器可达的被测应用暴露成云端浏览器可访问的公网 URL。 TunnelProvider 的形状为…** (1 connections) — `runtime/gherkai_runtime/tunnel.py`
- **隧道起不来 / provider 未知 / 前置缺失——调用方接住归「没开始执行就被拒」（退出码 2）。** (1 connections) — `runtime/gherkai_runtime/tunnel.py`
- **一条已建立隧道的事实（可序列化落盘 tunnel.json，供跨进程收尾）。** (1 connections) — `runtime/gherkai_runtime/tunnel.py`
- **替换进 job 文本的形态：凭据内嵌 URL（`https://user:pass@host`，ADR 0035 决策 4 方案①——…** (1 connections) — `runtime/gherkai_runtime/tunnel.py`
- **生成隧道专用短命凭据：纯字母数字（规避 URL-encode，ADR 0035 决策 4），每 run 一换。** (1 connections) — `runtime/gherkai_runtime/tunnel.py`

## Relationships

- [Ngrok Tunnel Provider](Ngrok_Tunnel_Provider.md) (11 shared connections)
- [Job/Scenario Explain Model](Job-Scenario_Explain_Model.md) (4 shared connections)
- [Cloud Launcher & Fargate Adapters](Cloud_Launcher_%26_Fargate_Adapters.md) (1 shared connections)
- [Tunnel Host Orchestration](Tunnel_Host_Orchestration.md) (1 shared connections)
- [SQLite Event Log Adapter](SQLite_Event_Log_Adapter.md) (1 shared connections)
- [Tunnel Watch TTL Daemon](Tunnel_Watch_TTL_Daemon.md) (1 shared connections)
- [Job Origin Mapping](Job_Origin_Mapping.md) (1 shared connections)
- [Core Library Concepts & ADRs](Core_Library_Concepts_%26_ADRs.md) (1 shared connections)

## Source Files

- `runtime/gherkai_runtime/tunnel.py`
- `runtime/tests/test_tunnel.py`

## Audit Trail

- EXTRACTED: 32 (89%)
- INFERRED: 4 (11%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*