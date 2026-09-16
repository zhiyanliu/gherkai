# Runtime Composition & Tunnel Host

> 10 nodes · cohesion 0.22

## Key Concepts

- **gherkai_runtime/__init__.py** (12 connections) — `runtime/gherkai_runtime/__init__.py`
- **tunnel_host.py** (10 connections) — `runtime/gherkai_runtime/tunnel_host.py`
- **start_tunnel_for_jobs()** (7 connections) — `runtime/gherkai_runtime/tunnel_host.py`
- **TunnelSetup** (4 connections) — `runtime/gherkai_runtime/tunnel_host.py`
- **test_start_tunnel_for_jobs_propagates_tunnel_error()** (4 connections) — `runtime/tests/test_tunnel_host.py`
- **gherkai：产品本体 = 组合根共享层（ADR 0016「演进」节）。 知道产品的一切——引擎注册表与装配（compose）、local…** (1 connections) — `runtime/gherkai_runtime/__init__.py`
- **隧道宿主编排（ADR 0035 决策 3）：起隧道 + 映射 definition、守隧道到 run 终态。 **宿主** = 持有隧道 agent…** (1 connections) — `runtime/gherkai_runtime/tunnel_host.py`
- **隧道就绪后的三件产物：映射过的 definition + 隧道模式的额外请求头 + 隧道事实（收尾凭据）。** (1 connections) — `runtime/gherkai_runtime/tunnel_host.py`
- **起隧道并把 definition 里的 origin 映射成公网 URL（ADR 0035 决策 1/2/4）。 起不来（provider 未知 /…** (1 connections) — `runtime/gherkai_runtime/tunnel_host.py`
- **provider 起不来 → TunnelError 直接冒给调用方（皮归「没开跑就被拒」退 2，不在本层吞成哨兵）。** (1 connections) — `runtime/tests/test_tunnel_host.py`

## Relationships

- [Tunnel Host Watchdog](Tunnel_Host_Watchdog.md) (7 shared connections)
- [Runtime Composition Root](Runtime_Composition_Root.md) (2 shared connections)
- [Tunnel Provider Factory](Tunnel_Provider_Factory.md) (2 shared connections)
- [CLI Command Entry Points](CLI_Command_Entry_Points.md) (1 shared connections)
- [JSON Contract Guards](JSON_Contract_Guards.md) (1 shared connections)
- [CLI Run Command Tests](CLI_Run_Command_Tests.md) (1 shared connections)
- [Submit & Tunnel CLI Tests](Submit_%26_Tunnel_CLI_Tests.md) (1 shared connections)
- [SQLite Event Log](SQLite_Event_Log.md) (1 shared connections)
- [Cloud Target & Worker Resolution](Cloud_Target_%26_Worker_Resolution.md) (1 shared connections)
- [Resource Naming Source](Resource_Naming_Source.md) (1 shared connections)
- [Worker Variant Resolution](Worker_Variant_Resolution.md) (1 shared connections)
- [Cloud Boto3 Guards & EventLog](Cloud_Boto3_Guards_%26_EventLog.md) (1 shared connections)

## Source Files

- `runtime/gherkai_runtime/__init__.py`
- `runtime/gherkai_runtime/tunnel_host.py`
- `runtime/tests/test_tunnel_host.py`

## Audit Trail

- EXTRACTED: 31 (97%)
- INFERRED: 1 (3%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*