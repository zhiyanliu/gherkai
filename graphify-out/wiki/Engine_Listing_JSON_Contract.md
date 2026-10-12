# Engine Listing JSON Contract

> 24 nodes · cohesion 0.13

## Key Concepts

- **test_cli_json_contract.py** (19 connections) — `cli/tests/test_cli_json_contract.py`
- **_assert_documented()** (9 connections) — `cli/tests/test_cli_json_contract.py`
- **_sample_run_result()** (7 connections) — `cli/tests/test_cli_json_contract.py`
- **test_explain_json_keys_are_documented()** (6 connections) — `cli/tests/test_cli_json_contract.py`
- **_cmd_list_engines()** (5 connections) — `cli/gherkai_cli/__main__.py`
- **_probe_engines()** (5 connections) — `cli/gherkai_cli/__main__.py`
- **_mk()** (4 connections) — `cli/tests/test_cli_json_contract.py`
- **test_doctor_json_keys_are_documented()** (4 connections) — `cli/tests/test_cli_json_contract.py`
- **test_plan_json_keys_are_documented()** (4 connections) — `cli/tests/test_cli_json_contract.py`
- **_leaf_keys()** (3 connections) — `cli/tests/test_cli_json_contract.py`
- **_sample_evidence()** (3 connections) — `cli/tests/test_cli_json_contract.py`
- **test_list_engines_and_deterministic_json_keys_are_documented()** (3 connections) — `cli/tests/test_cli_json_contract.py`
- **test_run_json_keys_are_documented()** (3 connections) — `cli/tests/test_cli_json_contract.py`
- **test_status_json_keys_are_documented()** (3 connections) — `cli/tests/test_cli_json_contract.py`
- **gherkai_core/__init__.py** (3 connections) — `core/gherkai_core/__init__.py`
- **_documented_keys()** (2 connections) — `cli/tests/test_cli_json_contract.py`
- **两引擎各走一遍定位链（ADR 0037 决策 3）→ 机读行：{engine, available, cmd, cwd, source,…** (1 connections) — `cli/gherkai_cli/__main__.py`
- **列出各引擎 worker 的拉起命令 + 命中的定位链级别（ADR 0037 决策 3 的自省口）；miss 则打安装指引。 **恒以退出码 0…** (1 connections) — `cli/gherkai_cli/__main__.py`
- **`--json` 字段契约的护栏（ADR 0041 决策五）：真渲染器出样例 → 递归收全部键名 → 逐个断言出现在 docs/internals/cli-…** (1 connections) — `cli/tests/test_cli_json_contract.py`
- **手搭的 evidence 夹具（ADR 0042 决策一的 schema，固定键全填）——形状与两引擎映射测试用的真产物裁剪版一致。…** (1 connections) — `cli/tests/test_cli_json_contract.py`
- **explain 的样例由**真渲染器**从手搭 JobResult + evidence 夹具生成（否则 evidence 那批键根本不进比对）。** (1 connections) — `cli/tests/test_cli_json_contract.py`
- **递归收全部 dict 键名（只取键名本身，不含路径——文档按键名解释）。 opaque…** (1 connections) — `cli/tests/test_cli_json_contract.py`
- **把所有可选字段都填上（votes/cost/report_refs/argument 两种/extra…** (1 connections) — `cli/tests/test_cli_json_contract.py`
- **执行核心库（窄腰）：解析 .feature → 分组 scope → 调度 → 收集结果。零引擎依赖。** (1 connections) — `core/gherkai_core/__init__.py`

## Relationships

- [CLI Command Entry Points](CLI_Command_Entry_Points.md) (3 shared connections)
- [CLI Plan And Doctor Tests](CLI_Plan_And_Doctor_Tests.md) (2 shared connections)
- [Plan Explain Rendering](Plan_Explain_Rendering.md) (2 shared connections)
- [Job Explain Data Model](Job_Explain_Data_Model.md) (2 shared connections)
- [Text UI Rendering](Text_UI_Rendering.md) (1 shared connections)
- [Deploy Provider Discovery](Deploy_Provider_Discovery.md) (1 shared connections)
- [Result Store Adapters](Result_Store_Adapters.md) (1 shared connections)
- [Deploy Command Frontend](Deploy_Command_Frontend.md) (1 shared connections)
- [SSM Paths And Compose](SSM_Paths_And_Compose.md) (1 shared connections)
- [Result Tree Rendering](Result_Tree_Rendering.md) (1 shared connections)
- [Doctor Self-check Tests](Doctor_Self-check_Tests.md) (1 shared connections)
- [Explain Output Rendering](Explain_Output_Rendering.md) (1 shared connections)

## Source Files

- `cli/gherkai_cli/__main__.py`
- `cli/tests/test_cli_json_contract.py`
- `core/gherkai_core/__init__.py`

## Audit Trail

- EXTRACTED: 52 (95%)
- INFERRED: 3 (5%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*