# Provider Resolution and Doctor

> 20 nodes · cohesion 0.12

## Key Concepts

- **_cmd_doctor()** (11 connections) — `cli/gherkai_cli/__main__.py`
- **resolve_provider()** (7 connections) — `cli/gherkai_cli/deploy.py`
- **_doctor_cloud()** (6 connections) — `cli/gherkai_cli/__main__.py`
- **_doctor_provider()** (6 connections) — `cli/gherkai_cli/__main__.py`
- **provider_entry_points()** (5 connections) — `cli/gherkai_cli/deploy.py`
- **_cmd_list_engines()** (5 connections) — `cli/gherkai_cli/__main__.py`
- **_probe_engines()** (5 connections) — `cli/gherkai_cli/__main__.py`
- **.add()** (5 connections) — `runtime/gherkai_runtime/textui.py`
- **_doctor_worker_grace()** (4 connections) — `cli/gherkai_cli/__main__.py`
- **_peek_deploy_provider()** (4 connections) — `cli/gherkai_cli/__main__.py`
- **已装的 provider entry point（按名排序、**不加载**）——零个/一个/多个的分叉全据此判。** (1 connections) — `cli/gherkai_cli/deploy.py`
- **按 `--provider` 值（或唯一性）选出 provider 并加载 → `(provider, None)`；失败 → `(None,…** (1 connections) — `cli/gherkai_cli/deploy.py`
- **两引擎各走一遍定位链（ADR 0037 决策 3）→ 机读行：{engine, available, cmd, cwd, source,…** (1 connections) — `cli/gherkai_cli/__main__.py`
- **列出各引擎 worker 的拉起命令 + 命中的定位链级别（ADR 0037 决策 3 的自省口）；miss 则打安装指引。 **恒以退出码 0…** (1 connections) — `cli/gherkai_cli/__main__.py`
- **只读自检（ADR 0041 决策四）：一个入口、按组件分组；每项 {section, name, ok, required, detail}。 **退出码只看…** (1 connections) — `cli/gherkai_cli/__main__.py`
- **doctor 的 aws / backend 两段（拆出来只为 `_cmd_doctor` 读得下去）：region → 身份 → 版本 → 资源 → 默认…** (1 connections) — `cli/gherkai_cli/__main__.py`
- **doctor 的 `backend.worker.grace` 行：引擎 worker 自报的最短收尾宽限 vs 云端 task-def 的停止宽限。…** (1 connections) — `cli/gherkai_cli/__main__.py`
- **从 argv 窥出「是不是 deploy/destroy、有没有 --provider」，据此解析部署 provider（ADR 0037 决策 6）。…** (1 connections) — `cli/gherkai_cli/__main__.py`
- **doctor 的 provider 段：按 entry point 结构化判「没装 / 装了多个 / 装了但坏 / 装了且可自检」，别靠匹配错误文案。…** (1 connections) — `cli/gherkai_cli/__main__.py`
- **EntryPoint** (1 connections)

## Relationships

- [CLI Command Handlers](CLI_Command_Handlers.md) (8 shared connections)
- [Terminal UI Rendering](Terminal_UI_Rendering.md) (3 shared connections)
- [CLI Entry and Plan](CLI_Entry_and_Plan.md) (3 shared connections)
- [Deploy Command Frontend](Deploy_Command_Frontend.md) (2 shared connections)
- [Deploy/Destroy Dispatch](Deploy-Destroy_Dispatch.md) (1 shared connections)
- [Deploy Command Frontend Tests](Deploy_Command_Frontend_Tests.md) (1 shared connections)
- [CLI Parser Construction](CLI_Parser_Construction.md) (1 shared connections)
- [Plan CLI Command](Plan_CLI_Command.md) (1 shared connections)
- [Explain Rendering](Explain_Rendering.md) (1 shared connections)
- [JSON Contract Guards](JSON_Contract_Guards.md) (1 shared connections)

## Source Files

- `cli/gherkai_cli/__main__.py`
- `cli/gherkai_cli/deploy.py`
- `runtime/gherkai_runtime/textui.py`

## Audit Trail

- EXTRACTED: 44 (98%)
- INFERRED: 1 (2%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*