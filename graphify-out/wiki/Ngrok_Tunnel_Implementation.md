# Ngrok Tunnel Implementation

> 10 nodes · cohesion 0.24

## Key Concepts

- **NgrokTunnel** (12 connections) — `runtime/gherkai_runtime/tunnel.py`
- **_fake_popen_writing_log()** (5 connections) — `runtime/tests/test_tunnel.py`
- **test_ngrok_start_timeout_reports_authtoken_hint()** (4 connections) — `runtime/tests/test_tunnel.py`
- **test_ngrok_start_spawns_agent_and_reads_log()** (3 connections) — `runtime/tests/test_tunnel.py`
- **test_ngrok_start_without_auth_skips_policy()** (3 connections) — `runtime/tests/test_tunnel.py`
- **test_ngrok_binary_missing_reports_install_hint()** (2 connections) — `runtime/tests/test_tunnel.py`
- **.__init__()** (1 connections) — `runtime/gherkai_runtime/tunnel.py`
- **ngrok 实现（ADR 0035 决策 1，当前唯一 provider）。 spawn `ngrok http <origin> --log <file>…** (1 connections) — `runtime/gherkai_runtime/tunnel.py`
- **日志里一直没有 started tunnel（agent 挂着不就绪）→ 超时 TunnelError，点名 authtoken 引导排错。** (1 connections) — `runtime/tests/test_tunnel.py`
- **fake agent：spawn 时往 --log 指定的文件写 started tunnel 行（None=不写，覆盖超时路径）。** (1 connections) — `runtime/tests/test_tunnel.py`

## Relationships

- [Tunnel Origin Mapping](Tunnel_Origin_Mapping.md) (7 shared connections)
- [Tunnel Provider Factory](Tunnel_Provider_Factory.md) (2 shared connections)
- [Job Explain & S3 Offload](Job_Explain_%26_S3_Offload.md) (1 shared connections)
- [Submit & Tunnel CLI Tests](Submit_%26_Tunnel_CLI_Tests.md) (1 shared connections)

## Source Files

- `runtime/gherkai_runtime/tunnel.py`
- `runtime/tests/test_tunnel.py`

## Audit Trail

- EXTRACTED: 20 (91%)
- INFERRED: 2 (9%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*