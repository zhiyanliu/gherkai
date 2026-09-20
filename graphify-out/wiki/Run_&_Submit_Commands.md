# Run & Submit Commands

> 27 nodes · cohesion 0.11

## Key Concepts

- **_progress()** (30 connections) — `cli/gherkai_cli/__main__.py`
- **_cmd_run()** (13 connections) — `cli/gherkai_cli/__main__.py`
- **_cmd_submit()** (10 connections) — `cli/gherkai_cli/__main__.py`
- **_plan_and_preflight()** (10 connections) — `cli/gherkai_cli/__main__.py`
- **_cloud_worker_variant_gate()** (6 connections) — `cli/gherkai_cli/__main__.py`
- **_print_artifact_lines()** (6 connections) — `cli/gherkai_cli/__main__.py`
- **_submit_cloud()** (6 connections) — `cli/gherkai_cli/__main__.py`
- **_build_run_meta()** (5 connections) — `cli/gherkai_cli/__main__.py`
- **_resolve_steps_dir_for_backend()** (5 connections) — `cli/gherkai_cli/__main__.py`
- **_setup_tunnel()** (5 connections) — `cli/gherkai_cli/__main__.py`
- **_validate_worker_variant()** (5 connections) — `cli/gherkai_cli/__main__.py`
- **_preflight_worker_runtimes()** (4 connections) — `cli/gherkai_cli/__main__.py`
- **_worker_meta_fields()** (4 connections) — `cli/gherkai_cli/__main__.py`
- **test_artifact_lines_report_write_failure_falls_back_to_a_note()** (3 connections) — `cli/tests/test_main.py`
- **`--expose-local` 的 argparse 侧接线：编排在 `gherkai_runtime.tunnel_host`（ADR 0035 决策…** (1 connections) — `cli/gherkai_cli/__main__.py`
- **`run` 与 `submit` 的共享前置（同一序列，次序本身是判据）：入口 flag 校验 → plan → steps 目录解析 → 本机后端…** (1 connections) — `cli/gherkai_cli/__main__.py`
- **组装 definition（ADR 0016/0027）：新 run_id + 创建时刻 + plan 产出的 jobs + run 级执行参数。 `run`…** (1 connections) — `cli/gherkai_cli/__main__.py`
- **进度/诊断输出 → stderr（业界惯例：stdout 留给该命令的核心产出/数据，stderr 给所有诊断）。 这样 `gherkai run ……** (1 connections) — `cli/gherkai_cli/__main__.py`
- **产物落点三行（报告 / 运行元信息 / 判定明细）→ stderr：**`run` 结束与 `status` 终态共用这一份**…** (1 connections) — `cli/gherkai_cli/__main__.py`
- **[无状态批量运行] 提交完就走（ADR 0034）：plan → 写 RunMeta+全 pending → 起首轮推进 → 打印 run_id →…** (1 connections) — `cli/gherkai_cli/__main__.py`
- **cloud preflight 的**第三道闸**：把 `--worker-variant`（缺省为部署级默认指针）解析成本 run 用到的 每个引擎的…** (1 connections) — `cli/gherkai_cli/__main__.py`
- **variant 解析结果 → definition 字段（ADR 0038）：人读的 variant 名 + 引擎 → revision ARN。…** (1 connections) — `cli/gherkai_cli/__main__.py`
- **cloud submit：只 create_run 写 definition 到 DDB（不起 task）→ 云端 Lambda 事件驱动链接管推进。…** (1 connections) — `cli/gherkai_cli/__main__.py`
- **`_resolve_steps_dir` + 云端后端清零（ADR 0037 决策 4）：云端后端 steps…** (1 connections) — `cli/gherkai_cli/__main__.py`
- **本次 plan 用到的各引擎：worker 运行时能否定位 + 能力自述能否完成（ADR 0037 决策 3/4）。 - 定位链四级全 miss →…** (1 connections) — `cli/gherkai_cli/__main__.py`
- *... and 2 more nodes in this community*

## Relationships

- [CLI Command Dispatch](CLI_Command_Dispatch.md) (24 shared connections)
- [Doctor & Skill Install](Doctor_%26_Skill_Install.md) (4 shared connections)
- [Status Command](Status_Command.md) (4 shared connections)
- [Explain Command](Explain_Command.md) (4 shared connections)
- [CLI Plan Command Behavior](CLI_Plan_Command_Behavior.md) (3 shared connections)
- [Tunnel Provider](Tunnel_Provider.md) (2 shared connections)
- [Run State Rendering](Run_State_Rendering.md) (2 shared connections)
- [Deploy Provider Resolution](Deploy_Provider_Resolution.md) (2 shared connections)
- [Run Metadata & S3 Offload](Run_Metadata_%26_S3_Offload.md) (1 shared connections)
- [Local Result Store](Local_Result_Store.md) (1 shared connections)
- [Explain Rendering Tests](Explain_Rendering_Tests.md) (1 shared connections)
- [CLI Entry Wiring Tests](CLI_Entry_Wiring_Tests.md) (1 shared connections)

## Source Files

- `cli/gherkai_cli/__main__.py`
- `cli/tests/test_main.py`

## Audit Trail

- EXTRACTED: 84 (97%)
- INFERRED: 3 (3%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*