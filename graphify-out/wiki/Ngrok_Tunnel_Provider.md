# Ngrok Tunnel Provider

> 12 nodes · cohesion 0.20

## Key Concepts

- **NgrokTunnel** (12 connections) — `runtime/gherkai_runtime/tunnel.py`
- **_fake_popen_writing_log()** (5 connections) — `runtime/tests/test_tunnel.py`
- **test_ngrok_agent_detaches_from_cli_process_group()** (4 connections) — `runtime/tests/test_tunnel.py`
- **test_ngrok_start_timeout_reports_authtoken_hint()** (4 connections) — `runtime/tests/test_tunnel.py`
- **test_ngrok_start_spawns_agent_and_reads_log()** (3 connections) — `runtime/tests/test_tunnel.py`
- **test_ngrok_start_without_auth_skips_policy()** (3 connections) — `runtime/tests/test_tunnel.py`
- **test_ngrok_binary_missing_reports_install_hint()** (2 connections) — `runtime/tests/test_tunnel.py`
- **.__init__()** (1 connections) — `runtime/gherkai_runtime/tunnel.py`
- **ngrok 实现（ADR 0035 决策 1，当前唯一 provider）。 spawn `ngrok http <origin> --log <file>…** (1 connections) — `runtime/gherkai_runtime/tunnel.py`
- **日志里一直没有 started tunnel（agent 挂着不就绪）→ 超时 TunnelError，点名 authtoken 引导排错。** (1 connections) — `runtime/tests/test_tunnel.py`
- ****真 spawn**（不 fake popen）：agent 必须落在自己的会话/进程组里（ADR 0035 决策 3）。 这条不能用 fake popen…** (1 connections) — `runtime/tests/test_tunnel.py`
- **fake agent：spawn 时往 --log 指定的文件写 started tunnel 行（None 表示不写，覆盖超时路径）。** (1 connections) — `runtime/tests/test_tunnel.py`

## Relationships

- [Tunnel Provider](Tunnel_Provider.md) (10 shared connections)
- [Run Metadata & S3 Offload](Run_Metadata_%26_S3_Offload.md) (1 shared connections)
- [Submit & Tunnel CLI Wiring](Submit_%26_Tunnel_CLI_Wiring.md) (1 shared connections)

## Source Files

- `runtime/gherkai_runtime/tunnel.py`
- `runtime/tests/test_tunnel.py`

## Audit Trail

- EXTRACTED: 23 (92%)
- INFERRED: 2 (8%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*