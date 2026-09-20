# Tunnel Provider

> 22 nodes · cohesion 0.14

## Key Concepts

- **test_tunnel.py** (24 connections) — `runtime/tests/test_tunnel.py`
- **tunnel.py** (13 connections) — `runtime/gherkai_runtime/tunnel.py`
- **stop_tunnel()** (11 connections) — `runtime/gherkai_runtime/tunnel.py`
- **TunnelInfo** (9 connections) — `runtime/gherkai_runtime/tunnel.py`
- **TunnelError** (8 connections) — `runtime/gherkai_runtime/tunnel.py`
- **make_tunnel()** (6 connections) — `runtime/gherkai_runtime/tunnel.py`
- **.start()** (5 connections) — `runtime/gherkai_runtime/tunnel.py`
- **_gen_auth()** (3 connections) — `runtime/gherkai_runtime/tunnel.py`
- **.mapped_base()** (2 connections) — `runtime/gherkai_runtime/tunnel.py`
- **test_make_tunnel_unknown_provider()** (2 connections) — `runtime/tests/test_tunnel.py`
- **test_mapped_base_embeds_credentials()** (2 connections) — `runtime/tests/test_tunnel.py`
- **test_mapped_base_without_auth_is_plain_url()** (2 connections) — `runtime/tests/test_tunnel.py`
- **test_stop_tunnel_idempotent_on_dead_pid()** (2 connections) — `runtime/tests/test_tunnel.py`
- **Exception** (1 connections)
- **隧道口子（ADR 0035）：把 CLI 所在机器可达的被测应用暴露成云端浏览器可访问的公网 URL。 TunnelProvider 的形状为…** (1 connections) — `runtime/gherkai_runtime/tunnel.py`
- **收尾：SIGTERM 隧道 agent 进程。幂等——进程已不在（重复收尾/自然退出）静默返回。** (1 connections) — `runtime/gherkai_runtime/tunnel.py`
- **按 `--tunnel <provider>` 选实现（ADR 0035 决策 1；当前唯一 ngrok，机制先行）。** (1 connections) — `runtime/gherkai_runtime/tunnel.py`
- **隧道起不来 / provider 未知 / 前置缺失——调用方接住归「没开始执行就被拒」（退出码 2）。** (1 connections) — `runtime/gherkai_runtime/tunnel.py`
- **一条已建立隧道的事实（可序列化落盘 tunnel.json，供跨进程收尾）。** (1 connections) — `runtime/gherkai_runtime/tunnel.py`
- **替换进 job 文本的形态：凭据内嵌 URL（`https://user:pass@host`，ADR 0035 决策 4 方案①——…** (1 connections) — `runtime/gherkai_runtime/tunnel.py`
- **生成隧道专用短命凭据：纯字母数字（规避 URL-encode，ADR 0035 决策 4），每 run 一换。** (1 connections) — `runtime/gherkai_runtime/tunnel.py`
- **tunnel 模块单测（ADR 0035）：origin 映射（纯逻辑）+ NgrokTunnel 编排（fake spawn/API，不真起 ngrok）。…** (1 connections) — `runtime/tests/test_tunnel.py`

## Relationships

- [Ngrok Tunnel Provider](Ngrok_Tunnel_Provider.md) (10 shared connections)
- [Origin URL Mapping](Origin_URL_Mapping.md) (6 shared connections)
- [Submit & Tunnel CLI Wiring](Submit_%26_Tunnel_CLI_Wiring.md) (3 shared connections)
- [Run State Rendering](Run_State_Rendering.md) (2 shared connections)
- [Tunnel Host Orchestration](Tunnel_Host_Orchestration.md) (2 shared connections)
- [Tunnel Host TTL Watch](Tunnel_Host_TTL_Watch.md) (2 shared connections)
- [Local Detached Execution](Local_Detached_Execution.md) (2 shared connections)
- [Run & Submit Commands](Run_%26_Submit_Commands.md) (2 shared connections)
- [Run Metadata & S3 Offload](Run_Metadata_%26_S3_Offload.md) (2 shared connections)
- [Detached Launcher Tests](Detached_Launcher_Tests.md) (1 shared connections)

## Source Files

- `runtime/gherkai_runtime/tunnel.py`
- `runtime/tests/test_tunnel.py`

## Audit Trail

- EXTRACTED: 59 (91%)
- INFERRED: 6 (9%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*