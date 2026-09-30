# Tunnel Origin Mapping

> 17 nodes · cohesion 0.18

## Key Concepts

- **test_tunnel.py** (24 connections) — `runtime/tests/test_tunnel.py`
- **TunnelInfo** (9 connections) — `runtime/gherkai_runtime/tunnel.py`
- **map_origin_in_jobs()** (8 connections) — `runtime/gherkai_runtime/tunnel.py`
- **_job_with()** (8 connections) — `runtime/tests/test_tunnel.py`
- **test_map_replaces_docstring_and_datatable()** (4 connections) — `runtime/tests/test_tunnel.py`
- **test_map_leaves_non_matching_urls_untouched()** (3 connections) — `runtime/tests/test_tunnel.py`
- **test_map_replaces_step_text_prefix()** (3 connections) — `runtime/tests/test_tunnel.py`
- **.mapped_base()** (2 connections) — `runtime/gherkai_runtime/tunnel.py`
- **StepArgument** (2 connections)
- **test_mapped_base_embeds_credentials()** (2 connections) — `runtime/tests/test_tunnel.py`
- **test_mapped_base_without_auth_is_plain_url()** (2 connections) — `runtime/tests/test_tunnel.py`
- **Job** (1 connections)
- **把 job 文本中的 origin 前缀替换成隧道 base（ADR 0035 决策 2：job-in 前、worker/AI 无感）。 替换面为…** (1 connections) — `runtime/gherkai_runtime/tunnel.py`
- **一条已建立隧道的事实（可序列化落盘 tunnel.json，供跨进程收尾）。** (1 connections) — `runtime/gherkai_runtime/tunnel.py`
- **替换进 job 文本的形态：凭据内嵌 URL（`https://user:pass@host`，ADR 0035 决策 4 方案①——…** (1 connections) — `runtime/gherkai_runtime/tunnel.py`
- **Job** (1 connections)
- **tunnel 模块单测（ADR 0035）：origin 映射（纯逻辑）+ NgrokTunnel 编排（fake spawn/API，不真起 ngrok）。…** (1 connections) — `runtime/tests/test_tunnel.py`

## Relationships

- [Tunnel Provider Seam](Tunnel_Provider_Seam.md) (7 shared connections)
- [Ngrok Tunnel Implementation](Ngrok_Tunnel_Implementation.md) (6 shared connections)
- [Run Definition Domain Model](Run_Definition_Domain_Model.md) (5 shared connections)
- [Tunnel Process Teardown](Tunnel_Process_Teardown.md) (3 shared connections)
- [Tunnel Host Orchestration](Tunnel_Host_Orchestration.md) (1 shared connections)
- [Core Adapters Documentation](Core_Adapters_Documentation.md) (1 shared connections)

## Source Files

- `runtime/gherkai_runtime/tunnel.py`
- `runtime/tests/test_tunnel.py`

## Audit Trail

- EXTRACTED: 46 (96%)
- INFERRED: 2 (4%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*