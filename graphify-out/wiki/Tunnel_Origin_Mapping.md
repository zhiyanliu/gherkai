# Tunnel Origin Mapping

> 16 nodes · cohesion 0.20

## Key Concepts

- **test_tunnel.py** (24 connections) — `runtime/tests/test_tunnel.py`
- **stop_tunnel()** (10 connections) — `runtime/gherkai_runtime/tunnel.py`
- **map_origin_in_jobs()** (8 connections) — `runtime/gherkai_runtime/tunnel.py`
- **_job_with()** (8 connections) — `runtime/tests/test_tunnel.py`
- **test_map_replaces_docstring_and_datatable()** (4 connections) — `runtime/tests/test_tunnel.py`
- **test_ngrok_agent_detaches_from_cli_process_group()** (4 connections) — `runtime/tests/test_tunnel.py`
- **test_map_leaves_non_matching_urls_untouched()** (3 connections) — `runtime/tests/test_tunnel.py`
- **test_map_replaces_step_text_prefix()** (3 connections) — `runtime/tests/test_tunnel.py`
- **StepArgument** (2 connections)
- **test_stop_tunnel_idempotent_on_dead_pid()** (2 connections) — `runtime/tests/test_tunnel.py`
- **Job** (1 connections)
- **收尾：SIGTERM 隧道 agent 进程。幂等——进程已不在（重复收尾/自然退出）静默返回。** (1 connections) — `runtime/gherkai_runtime/tunnel.py`
- **把 job 文本中的 origin 前缀替换成隧道 base（ADR 0035 决策 2：job-in 前、worker/AI 无感）。 替换面 =…** (1 connections) — `runtime/gherkai_runtime/tunnel.py`
- **Job** (1 connections)
- **tunnel 模块单测（ADR 0035）：origin 映射（纯逻辑）+ NgrokTunnel 编排（fake spawn/API，不真起 ngrok）。…** (1 connections) — `runtime/tests/test_tunnel.py`
- ****真 spawn**（不 fake popen）：agent 必须落在自己的会话/进程组里（ADR 0035 决策 3）。 这条不能用 fake popen…** (1 connections) — `runtime/tests/test_tunnel.py`

## Relationships

- [Ngrok Tunnel Implementation](Ngrok_Tunnel_Implementation.md) (7 shared connections)
- [Tunnel Provider Factory](Tunnel_Provider_Factory.md) (6 shared connections)
- [Tunnel Info Credentials](Tunnel_Info_Credentials.md) (3 shared connections)
- [SQLite Event Log](SQLite_Event_Log.md) (2 shared connections)
- [CLI Command Entry Points](CLI_Command_Entry_Points.md) (2 shared connections)
- [Job Explain & S3 Offload](Job_Explain_%26_S3_Offload.md) (2 shared connections)
- [Runtime Composition & Tunnel Host](Runtime_Composition_%26_Tunnel_Host.md) (1 shared connections)
- [Tunnel Host Watchdog](Tunnel_Host_Watchdog.md) (1 shared connections)
- [Cloud Boto3 Guards & EventLog](Cloud_Boto3_Guards_%26_EventLog.md) (1 shared connections)
- [Submit & Tunnel CLI Tests](Submit_%26_Tunnel_CLI_Tests.md) (1 shared connections)

## Source Files

- `runtime/gherkai_runtime/tunnel.py`
- `runtime/tests/test_tunnel.py`

## Audit Trail

- EXTRACTED: 48 (96%)
- INFERRED: 2 (4%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*