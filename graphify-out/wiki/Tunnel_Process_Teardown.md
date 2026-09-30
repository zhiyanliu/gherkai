# Tunnel Process Teardown

> 5 nodes · cohesion 0.40

## Key Concepts

- **stop_tunnel()** (11 connections) — `runtime/gherkai_runtime/tunnel.py`
- **test_ngrok_agent_detaches_from_cli_process_group()** (4 connections) — `runtime/tests/test_tunnel.py`
- **test_stop_tunnel_idempotent_on_dead_pid()** (2 connections) — `runtime/tests/test_tunnel.py`
- **收尾：SIGTERM 隧道 agent 进程。幂等——进程已不在（重复收尾/自然退出）静默返回。** (1 connections) — `runtime/gherkai_runtime/tunnel.py`
- ****真 spawn**（不 fake popen）：agent 必须落在自己的会话/进程组里（ADR 0035 决策 3）。 这条不能用 fake popen…** (1 connections) — `runtime/tests/test_tunnel.py`

## Relationships

- [Tunnel Origin Mapping](Tunnel_Origin_Mapping.md) (3 shared connections)
- [Local Detached Reconcile](Local_Detached_Reconcile.md) (2 shared connections)
- [Tunnel Provider Seam](Tunnel_Provider_Seam.md) (2 shared connections)
- [CLI Command Entrypoints](CLI_Command_Entrypoints.md) (2 shared connections)
- [Tunnel Host Watchdog](Tunnel_Host_Watchdog.md) (1 shared connections)
- [Ngrok Tunnel Implementation](Ngrok_Tunnel_Implementation.md) (1 shared connections)

## Source Files

- `runtime/gherkai_runtime/tunnel.py`
- `runtime/tests/test_tunnel.py`

## Audit Trail

- EXTRACTED: 13 (87%)
- INFERRED: 2 (13%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*