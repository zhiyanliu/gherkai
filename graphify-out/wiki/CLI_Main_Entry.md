# CLI Main Entry

> 24 nodes · cohesion 0.11

## Key Concepts

- **gherkai_cli/__main__.py** (47 connections) — `cli/gherkai_cli/__main__.py`
- **_build_parser()** (8 connections) — `cli/gherkai_cli/__main__.py`
- **_cloud_skew_gate()** (7 connections) — `cli/gherkai_cli/__main__.py`
- **_submit_cloud()** (7 connections) — `cli/gherkai_cli/__main__.py`
- **_cloud_worker_variant_gate()** (6 connections) — `cli/gherkai_cli/__main__.py`
- **_dist_version()** (6 connections) — `cli/gherkai_cli/__main__.py`
- **_installed_version()** (5 connections) — `cli/gherkai_cli/__main__.py`
- **_cmd_reconcile()** (4 connections) — `cli/gherkai_cli/__main__.py`
- **_runtime_version()** (4 connections) — `runtime/gherkai_runtime/compose.py`
- **_cmd_list_engines()** (3 connections) — `cli/gherkai_cli/__main__.py`
- **_cmd_tunnel_watch()** (3 connections) — `cli/gherkai_cli/__main__.py`
- **_tunnel_providers()** (2 connections) — `cli/gherkai_cli/__main__.py`
- **ArgumentParser** (1 connections)
- **gherkai：执行核心库的命令行皮（ADR 0016）。 皮做四件事：解析参数 → 读 feature（compose）→ 注入引擎 resolver 跑…** (1 connections) — `cli/gherkai_cli/__main__.py`
- **per-run 进程入口（submit setsid fork 它，非用户直接调）：跑 reconcile loop 到全 done 自退（ADR…** (1 connections) — `cli/gherkai_cli/__main__.py`
- **隧道守护进程入口（cloud submit setsid fork 它，非用户直接调，ADR 0035 决策 3）。 守护主体在…** (1 connections) — `cli/gherkai_cli/__main__.py`
- **发行版本字符串（唯一真源 = git tag，经 uv-dynamic-versioning 写进包元数据，ADR 0037 决策 2b；…** (1 connections) — `cli/gherkai_cli/__main__.py`
- **给**契约比对**用的版本（skew 三态 / worker variant 解析 / 交 provider 写版本戳，ADR 0037 决策…** (1 connections) — `cli/gherkai_cli/__main__.py`
- **列出各引擎 worker 的拉起命令 + 命中的定位链级别（ADR 0037 决策 3 的自省口）；miss 则打安装指引。 **恒退…** (1 connections) — `cli/gherkai_cli/__main__.py`
- **cloud 路径的**第一道闸**：CLI 与后端的版本 skew 三态（ADR 0037 决策 7）。 返回 `(退出码 or None, 后端版本戳 or…** (1 connections) — `cli/gherkai_cli/__main__.py`
- **cloud preflight 的**第三道闸**：把 `--worker-variant`（缺省 = 部署级默认指针）解析成本 run 用到的 每个引擎的…** (1 connections) — `cli/gherkai_cli/__main__.py`
- **cloud submit：只 create_run 写 definition 到 DDB（不起 task）→ 云端 Lambda 事件驱动链接管推进。…** (1 connections) — `cli/gherkai_cli/__main__.py`
- **建主 parser。`provider`（部署 provider，由 `main` 先窥 argv 解析出来）给了就让它贴自己的 flag。 **为何…** (1 connections) — `cli/gherkai_cli/__main__.py`
- **本包（`gherkai-runtime`）的发行版本：定位链第四级的 pin 值。未装成包（源码直跑）→ None。** (1 connections) — `runtime/gherkai_runtime/compose.py`

## Relationships

- [CLI Run/Submit Commands](CLI_Run-Submit_Commands.md) (20 shared connections)
- [CLI Run Entry Tests](CLI_Run_Entry_Tests.md) (6 shared connections)
- [Status Command Rendering](Status_Command_Rendering.md) (4 shared connections)
- [Engine Ports & Adapters](Engine_Ports_%26_Adapters.md) (3 shared connections)
- [Deploy Command Shell Tests](Deploy_Command_Shell_Tests.md) (3 shared connections)
- [Deploy Provider Discovery](Deploy_Provider_Discovery.md) (3 shared connections)
- [Plan Command & Rendering](Plan_Command_%26_Rendering.md) (3 shared connections)
- [Deploy/Destroy CLI Commands](Deploy-Destroy_CLI_Commands.md) (3 shared connections)
- [Run Result Verdict Model](Run_Result_Verdict_Model.md) (2 shared connections)
- [List Deterministic CLI Command](List_Deterministic_CLI_Command.md) (2 shared connections)
- [Tunnel CLI Wiring Tests](Tunnel_CLI_Wiring_Tests.md) (1 shared connections)
- [Resource Naming Source](Resource_Naming_Source.md) (1 shared connections)

## Source Files

- `cli/gherkai_cli/__main__.py`
- `runtime/gherkai_runtime/compose.py`

## Audit Trail

- EXTRACTED: 82 (98%)
- INFERRED: 2 (2%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*