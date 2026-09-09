# Tunnel Cleanup

> 5 nodes · cohesion 0.40

## Key Concepts

- **stop_tunnel()** (10 connections) — `runtime/gherkai_runtime/tunnel.py`
- **cleanup_tunnel()** (3 connections) — `runtime/gherkai_runtime/detached.py`
- **test_stop_tunnel_idempotent_on_dead_pid()** (2 connections) — `runtime/tests/test_tunnel.py`
- **收尾者（per-run 终态后 / status --wait 接力后）拆隧道：有 tunnel.json 才动作，幂等。** (1 connections) — `runtime/gherkai_runtime/detached.py`
- **收尾：SIGTERM 隧道 agent 进程。幂等——进程已不在（重复收尾/自然退出）静默返回。** (1 connections) — `runtime/gherkai_runtime/tunnel.py`

## Relationships

- [Ngrok Tunnel Provider](Ngrok_Tunnel_Provider.md) (3 shared connections)
- [Local Detached Run Wiring](Local_Detached_Run_Wiring.md) (2 shared connections)
- [CLI Run/Submit Commands](CLI_Run-Submit_Commands.md) (2 shared connections)
- [Tunnel Host TTL Watchdog](Tunnel_Host_TTL_Watchdog.md) (1 shared connections)
- [Local Tunnel Exposure](Local_Tunnel_Exposure.md) (1 shared connections)

## Source Files

- `runtime/gherkai_runtime/detached.py`
- `runtime/gherkai_runtime/tunnel.py`
- `runtime/tests/test_tunnel.py`

## Audit Trail

- EXTRACTED: 11 (85%)
- INFERRED: 2 (15%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*