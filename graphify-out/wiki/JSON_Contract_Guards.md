# JSON Contract Guards

> 20 nodes · cohesion 0.17

## Key Concepts

- **test_cli_json_contract.py** (19 connections) — `cli/tests/test_cli_json_contract.py`
- **_assert_documented()** (9 connections) — `cli/tests/test_cli_json_contract.py`
- **_sample_run_result()** (7 connections) — `cli/tests/test_cli_json_contract.py`
- **test_explain_json_keys_are_documented()** (6 connections) — `cli/tests/test_cli_json_contract.py`
- **_mk()** (4 connections) — `cli/tests/test_cli_json_contract.py`
- **test_plan_json_keys_are_documented()** (4 connections) — `cli/tests/test_cli_json_contract.py`
- **_leaf_keys()** (3 connections) — `cli/tests/test_cli_json_contract.py`
- **_sample_evidence()** (3 connections) — `cli/tests/test_cli_json_contract.py`
- **test_doctor_json_keys_are_documented()** (3 connections) — `cli/tests/test_cli_json_contract.py`
- **test_list_engines_and_deterministic_json_keys_are_documented()** (3 connections) — `cli/tests/test_cli_json_contract.py`
- **test_run_json_keys_are_documented()** (3 connections) — `cli/tests/test_cli_json_contract.py`
- **test_status_json_keys_are_documented()** (3 connections) — `cli/tests/test_cli_json_contract.py`
- **_documented_keys()** (2 connections) — `cli/tests/test_cli_json_contract.py`
- **gherkai_core/__init__.py** (2 connections) — `core/gherkai_core/__init__.py`
- **`--json` 字段契约的护栏（ADR 0041 决策五）：真渲染器出样例 → 递归收全部键名 → 逐个断言出现在 docs/guides/cli-…** (1 connections) — `cli/tests/test_cli_json_contract.py`
- **手搭的 evidence 夹具（ADR 0042 决策一的 schema，固定键全填）——形状与两引擎映射测试用的真产物裁剪版一致。…** (1 connections) — `cli/tests/test_cli_json_contract.py`
- **explain 的样例由**真渲染器**从手搭 JobResult + evidence 夹具生成（否则 evidence 那批键根本不进比对）。** (1 connections) — `cli/tests/test_cli_json_contract.py`
- **递归收全部 dict 键名（只取键名本身，不含路径——文档按键名解释）。 opaque =…** (1 connections) — `cli/tests/test_cli_json_contract.py`
- **把所有可选字段都填上（votes/cost/report_refs/argument 两种/extra…** (1 connections) — `cli/tests/test_cli_json_contract.py`
- **执行核心库（窄腰）：解析 .feature → 分组 scope → 调度 → 收集结果。零引擎依赖。** (1 connections) — `core/gherkai_core/__init__.py`

## Relationships

- [Explain Rendering](Explain_Rendering.md) (3 shared connections)
- [DynamoDB RunStore Adapter](DynamoDB_RunStore_Adapter.md) (2 shared connections)
- [Job Explain & S3 Offload](Job_Explain_%26_S3_Offload.md) (2 shared connections)
- [Deploy CLI Shell](Deploy_CLI_Shell.md) (1 shared connections)
- [Runtime Composition & Tunnel Host](Runtime_Composition_%26_Tunnel_Host.md) (1 shared connections)
- [CLI Command Entry Points](CLI_Command_Entry_Points.md) (1 shared connections)
- [Text Render & Wording Guards](Text_Render_%26_Wording_Guards.md) (1 shared connections)
- [CLI Main Flow Tests](CLI_Main_Flow_Tests.md) (1 shared connections)
- [Doctor Self-Check Command](Doctor_Self-Check_Command.md) (1 shared connections)

## Source Files

- `cli/tests/test_cli_json_contract.py`
- `core/gherkai_core/__init__.py`

## Audit Trail

- EXTRACTED: 43 (96%)
- INFERRED: 2 (4%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*