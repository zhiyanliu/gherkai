# Ngrok Tunnel Provider

> 14 nodes · cohesion 0.23

## Key Concepts

- **test_tunnel.py** (24 connections) — `runtime/tests/test_tunnel.py`
- **NgrokTunnel** (12 connections) — `runtime/gherkai_runtime/tunnel.py`
- **_fake_popen_writing_log()** (5 connections) — `runtime/tests/test_tunnel.py`
- **test_ngrok_agent_detaches_from_cli_process_group()** (4 connections) — `runtime/tests/test_tunnel.py`
- **test_ngrok_start_timeout_reports_authtoken_hint()** (4 connections) — `runtime/tests/test_tunnel.py`
- **test_ngrok_start_spawns_agent_and_reads_log()** (3 connections) — `runtime/tests/test_tunnel.py`
- **test_ngrok_start_without_auth_skips_policy()** (3 connections) — `runtime/tests/test_tunnel.py`
- **test_ngrok_binary_missing_reports_install_hint()** (2 connections) — `runtime/tests/test_tunnel.py`
- **.__init__()** (1 connections) — `runtime/gherkai_runtime/tunnel.py`
- **ngrok 实现（ADR 0035 决策 1，当前唯一 provider）。 spawn `ngrok http <origin> --log <file>…** (1 connections) — `runtime/gherkai_runtime/tunnel.py`
- **tunnel 模块单测（ADR 0035）：origin 映射（纯逻辑）+ NgrokTunnel 编排（fake spawn/API，不真起 ngrok）。…** (1 connections) — `runtime/tests/test_tunnel.py`
- **日志里一直没有 started tunnel（agent 挂着不就绪）→ 超时 TunnelError，点名 authtoken 引导排错。** (1 connections) — `runtime/tests/test_tunnel.py`
- ****真 spawn**（不 fake popen）：agent 必须落在自己的会话/进程组里（ADR 0035 决策 3）。 这条不能用 fake popen…** (1 connections) — `runtime/tests/test_tunnel.py`
- **fake agent：spawn 时往 --log 指定的文件写 started tunnel 行（None=不写，覆盖超时路径）。** (1 connections) — `runtime/tests/test_tunnel.py`

## Relationships

- [Local Tunnel Exposure](Local_Tunnel_Exposure.md) (6 shared connections)
- [Job Origin URL Mapping](Job_Origin_URL_Mapping.md) (5 shared connections)
- [Engine Ports & Adapters](Engine_Ports_%26_Adapters.md) (4 shared connections)
- [Tunnel Cleanup](Tunnel_Cleanup.md) (3 shared connections)
- [Tunnel Info Model](Tunnel_Info_Model.md) (3 shared connections)

## Source Files

- `runtime/gherkai_runtime/tunnel.py`
- `runtime/tests/test_tunnel.py`

## Audit Trail

- EXTRACTED: 40 (95%)
- INFERRED: 2 (5%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*