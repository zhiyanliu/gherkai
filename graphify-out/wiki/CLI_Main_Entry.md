# CLI Main Entry

> 18 nodes · cohesion 0.14

## Key Concepts

- **gherkai_cli/__main__.py** (47 connections) — `cli/gherkai_cli/__main__.py`
- **_build_parser()** (8 connections) — `cli/gherkai_cli/__main__.py`
- **_dist_version()** (6 connections) — `cli/gherkai_cli/__main__.py`
- **_validate_worker_variant()** (6 connections) — `cli/gherkai_cli/__main__.py`
- **_installed_version()** (5 connections) — `cli/gherkai_cli/__main__.py`
- **_runtime_version()** (4 connections) — `runtime/gherkai_runtime/compose.py`
- **_cmd_list_engines()** (3 connections) — `cli/gherkai_cli/__main__.py`
- **_cmd_tunnel_watch()** (3 connections) — `cli/gherkai_cli/__main__.py`
- **_tunnel_providers()** (2 connections) — `cli/gherkai_cli/__main__.py`
- **ArgumentParser** (1 connections)
- **gherkai：执行核心库的命令行皮（ADR 0016）。 皮做四件事：解析参数 → 读 feature（compose）→ 注入引擎 resolver 跑…** (1 connections) — `cli/gherkai_cli/__main__.py`
- **隧道守护进程入口（cloud submit setsid fork 它，非用户直接调，ADR 0035 决策 3）。 守护主体在…** (1 connections) — `cli/gherkai_cli/__main__.py`
- **发行版本字符串（唯一真源 = git tag，经 uv-dynamic-versioning 写进包元数据，ADR 0037 决策 2b；…** (1 connections) — `cli/gherkai_cli/__main__.py`
- **给**契约比对**用的版本（skew 三态 / worker variant 解析 / 交 provider 写版本戳，ADR 0037 决策…** (1 connections) — `cli/gherkai_cli/__main__.py`
- **列出各引擎 worker 的拉起命令 + 命中的定位链级别（ADR 0037 决策 3 的自省口）；miss 则打安装指引。 **恒退…** (1 connections) — `cli/gherkai_cli/__main__.py`
- **`--worker-variant` 入口校验 + local 档提示（对齐 `--max-concurrency` 的入口校验惯例，ADR 0038）。…** (1 connections) — `cli/gherkai_cli/__main__.py`
- **建主 parser。`provider`（部署 provider，由 `main` 先窥 argv 解析出来）给了就让它贴自己的 flag。 **为何…** (1 connections) — `cli/gherkai_cli/__main__.py`
- **本包（`gherkai-runtime`）的发行版本：定位链第四级的 pin 值。未装成包（源码直跑）→ None。** (1 connections) — `runtime/gherkai_runtime/compose.py`

## Relationships

- [CLI Plan & Submit](CLI_Plan_%26_Submit.md) (13 shared connections)
- [Cloud Submit Preflight Gates](Cloud_Submit_Preflight_Gates.md) (8 shared connections)
- [CLI Run Entry Tests](CLI_Run_Entry_Tests.md) (5 shared connections)
- [Run Status & Reconcile CLI](Run_Status_%26_Reconcile_CLI.md) (4 shared connections)
- [Engine Ports & Adapters](Engine_Ports_%26_Adapters.md) (3 shared connections)
- [Run Result Rendering](Run_Result_Rendering.md) (3 shared connections)
- [Deploy Command Shell](Deploy_Command_Shell.md) (3 shared connections)
- [Deploy Provider Discovery](Deploy_Provider_Discovery.md) (3 shared connections)
- [Deploy/Destroy Provider Dispatch](Deploy-Destroy_Provider_Dispatch.md) (3 shared connections)
- [Tunnel CLI Tests](Tunnel_CLI_Tests.md) (1 shared connections)
- [Runtime Naming Source](Runtime_Naming_Source.md) (1 shared connections)
- [Cloud Backend CLI Tests](Cloud_Backend_CLI_Tests.md) (1 shared connections)

## Source Files

- `cli/gherkai_cli/__main__.py`
- `runtime/gherkai_runtime/compose.py`

## Audit Trail

- EXTRACTED: 71 (99%)
- INFERRED: 1 (1%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*