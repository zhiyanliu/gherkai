# Tunnel Provider

> 14 nodes · cohesion 0.18

## Key Concepts

- **tunnel.py** (13 connections) — `runtime/gherkai_runtime/tunnel.py`
- **stop_tunnel()** (11 connections) — `runtime/gherkai_runtime/tunnel.py`
- **TunnelError** (8 connections) — `runtime/gherkai_runtime/tunnel.py`
- **make_tunnel()** (6 connections) — `runtime/gherkai_runtime/tunnel.py`
- **.start()** (5 connections) — `runtime/gherkai_runtime/tunnel.py`
- **_gen_auth()** (3 connections) — `runtime/gherkai_runtime/tunnel.py`
- **test_make_tunnel_unknown_provider()** (2 connections) — `runtime/tests/test_tunnel.py`
- **test_stop_tunnel_idempotent_on_dead_pid()** (2 connections) — `runtime/tests/test_tunnel.py`
- **Exception** (1 connections)
- **隧道口子（ADR 0035）：把 CLI 所在机器可达的被测应用暴露成云端浏览器可访问的公网 URL。 TunnelProvider 的形状为…** (1 connections) — `runtime/gherkai_runtime/tunnel.py`
- **收尾：SIGTERM 隧道 agent 进程。幂等——进程已不在（重复收尾/自然退出）静默返回。** (1 connections) — `runtime/gherkai_runtime/tunnel.py`
- **按 `--tunnel <provider>` 选实现（ADR 0035 决策 1；当前唯一 ngrok，机制先行）。** (1 connections) — `runtime/gherkai_runtime/tunnel.py`
- **隧道起不来 / provider 未知 / 前置缺失——调用方接住归「没开始执行就被拒」（退出码 2）。** (1 connections) — `runtime/gherkai_runtime/tunnel.py`
- **生成隧道专用短命凭据：纯字母数字（规避 URL-encode，ADR 0035 决策 4），每 run 一换。** (1 connections) — `runtime/gherkai_runtime/tunnel.py`

## Relationships

- [Ngrok Tunnel Provider](Ngrok_Tunnel_Provider.md) (11 shared connections)
- [Job Domain Models](Job_Domain_Models.md) (3 shared connections)
- [Tunnel Host Orchestration](Tunnel_Host_Orchestration.md) (2 shared connections)
- [Tunnel Host Daemon](Tunnel_Host_Daemon.md) (2 shared connections)
- [Local Detached Execution](Local_Detached_Execution.md) (2 shared connections)
- [CLI Command Handlers](CLI_Command_Handlers.md) (2 shared connections)
- [Local Reconcile Loop Tests](Local_Reconcile_Loop_Tests.md) (1 shared connections)
- [Tunnel Origin Mapping](Tunnel_Origin_Mapping.md) (1 shared connections)

## Source Files

- `runtime/gherkai_runtime/tunnel.py`
- `runtime/tests/test_tunnel.py`

## Audit Trail

- EXTRACTED: 36 (90%)
- INFERRED: 4 (10%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*