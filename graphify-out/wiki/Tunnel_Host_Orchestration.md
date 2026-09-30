# Tunnel Host Orchestration

> 11 nodes · cohesion 0.20

## Key Concepts

- **gherkai_runtime/__init__.py** (12 connections) — `runtime/gherkai_runtime/__init__.py`
- **tunnel_host.py** (10 connections) — `runtime/gherkai_runtime/tunnel_host.py`
- **start_tunnel_for_jobs()** (7 connections) — `runtime/gherkai_runtime/tunnel_host.py`
- **TunnelSetup** (4 connections) — `runtime/gherkai_runtime/tunnel_host.py`
- **test_start_tunnel_for_jobs_propagates_tunnel_error()** (4 connections) — `runtime/tests/test_tunnel_host.py`
- **test_start_tunnel_for_jobs_maps_and_injects_headers()** (3 connections) — `runtime/tests/test_tunnel_host.py`
- **gherkai：产品本体即组合根共享层（ADR 0016「演进」节）。 持有产品级知识——引擎注册表与装配（compose）、local…** (1 connections) — `runtime/gherkai_runtime/__init__.py`
- **隧道宿主编排（ADR 0035 决策 3）：起隧道 + 映射 definition、守隧道到 run 终态。 **宿主**指持有隧道 agent…** (1 connections) — `runtime/gherkai_runtime/tunnel_host.py`
- **隧道就绪后的三件产物：映射过的 definition + 隧道模式的额外请求头 + 隧道事实（收尾凭据）。** (1 connections) — `runtime/gherkai_runtime/tunnel_host.py`
- **起隧道并把 definition 里的 origin 映射成公网 URL（ADR 0035 决策 1/2/4）。 起不来（provider 未知 /…** (1 connections) — `runtime/gherkai_runtime/tunnel_host.py`
- **provider 起不来 → TunnelError 直接冒给调用方（前端归「没开始执行就被拒」、退出码 2，不在本层吞成哨兵）。** (1 connections) — `runtime/tests/test_tunnel_host.py`

## Relationships

- [Tunnel Host Watchdog](Tunnel_Host_Watchdog.md) (6 shared connections)
- [Run Definition Domain Model](Run_Definition_Domain_Model.md) (3 shared connections)
- [Tunnel Provider Seam](Tunnel_Provider_Seam.md) (2 shared connections)
- [CLI Test Fixtures](CLI_Test_Fixtures.md) (1 shared connections)
- [Engine Listing and JSON Contract](Engine_Listing_and_JSON_Contract.md) (1 shared connections)
- [CLI Run Wiring Tests](CLI_Run_Wiring_Tests.md) (1 shared connections)
- [Tunnel CLI Wiring Tests](Tunnel_CLI_Wiring_Tests.md) (1 shared connections)
- [Local Detached Reconcile](Local_Detached_Reconcile.md) (1 shared connections)
- [Composition Root Helpers](Composition_Root_Helpers.md) (1 shared connections)
- [SSM Path Naming](SSM_Path_Naming.md) (1 shared connections)
- [Rich Text UI Presentation](Rich_Text_UI_Presentation.md) (1 shared connections)
- [Resource Naming and Variants](Resource_Naming_and_Variants.md) (1 shared connections)

## Source Files

- `runtime/gherkai_runtime/__init__.py`
- `runtime/gherkai_runtime/tunnel_host.py`
- `runtime/tests/test_tunnel_host.py`

## Audit Trail

- EXTRACTED: 33 (97%)
- INFERRED: 1 (3%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*