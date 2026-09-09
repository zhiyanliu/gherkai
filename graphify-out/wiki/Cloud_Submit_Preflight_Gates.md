# Cloud Submit Preflight Gates

> 9 nodes · cohesion 0.28

## Key Concepts

- **_cmd_run()** (16 connections) — `cli/gherkai_cli/__main__.py`
- **_cloud_skew_gate()** (7 connections) — `cli/gherkai_cli/__main__.py`
- **_submit_cloud()** (7 connections) — `cli/gherkai_cli/__main__.py`
- **_cloud_worker_variant_gate()** (6 connections) — `cli/gherkai_cli/__main__.py`
- **_worker_meta_fields()** (4 connections) — `cli/gherkai_cli/__main__.py`
- **cloud 路径的**第一道闸**：CLI 与后端的版本 skew 三态（ADR 0037 决策 7）。 返回 `(退出码 or None, 后端版本戳 or…** (1 connections) — `cli/gherkai_cli/__main__.py`
- **cloud preflight 的**第三道闸**：把 `--worker-variant`（缺省 = 部署级默认指针）解析成本 run 用到的 每个引擎的…** (1 connections) — `cli/gherkai_cli/__main__.py`
- **variant 解析结果 → definition 字段（ADR 0038）：人读的 variant 名 + 引擎 → revision ARN。…** (1 connections) — `cli/gherkai_cli/__main__.py`
- **cloud submit：只 create_run 写 definition 到 DDB（不起 task）→ 云端 Lambda 事件驱动链接管推进。…** (1 connections) — `cli/gherkai_cli/__main__.py`

## Relationships

- [CLI Plan & Submit](CLI_Plan_%26_Submit.md) (9 shared connections)
- [CLI Main Entry](CLI_Main_Entry.md) (8 shared connections)
- [Run Status & Reconcile CLI](Run_Status_%26_Reconcile_CLI.md) (2 shared connections)
- [Run Result Rendering](Run_Result_Rendering.md) (2 shared connections)
- [Local Result Store](Local_Result_Store.md) (1 shared connections)
- [CLI Run Entry Tests](CLI_Run_Entry_Tests.md) (1 shared connections)
- [Tunnel Cleanup](Tunnel_Cleanup.md) (1 shared connections)

## Source Files

- `cli/gherkai_cli/__main__.py`

## Audit Trail

- EXTRACTED: 32 (94%)
- INFERRED: 2 (6%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*