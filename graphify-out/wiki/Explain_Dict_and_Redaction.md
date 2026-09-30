# Explain Dict and Redaction

> 21 nodes · cohesion 0.13

## Key Concepts

- **core/tests/test_redact.py** (11 connections) — `core/tests/test_redact.py`
- **gherkai_core/redact.py** (10 connections) — `core/gherkai_core/redact.py`
- **explain_to_dict()** (9 connections) — `cli/gherkai_cli/render.py`
- **redact_url_userinfo()** (9 connections) — `core/gherkai_core/redact.py`
- **redact_deep()** (8 connections) — `core/gherkai_core/redact.py`
- **test_json_field_boundary_is_not_crossed()** (3 connections) — `core/tests/test_redact.py`
- **test_redact_url_userinfo_cases()** (3 connections) — `core/tests/test_redact.py`
- **test_serialized_json_line_stays_valid_and_loses_credentials()** (3 connections) — `core/tests/test_redact.py`
- **test_none_passes_through()** (2 connections) — `core/tests/test_redact.py`
- **test_redact_deep_recurses_values_and_leaves_keys_and_non_strings()** (2 connections) — `core/tests/test_redact.py`
- **test_redact_deep_scalars()** (2 connections) — `core/tests/test_redact.py`
- **把 JobResult 列表 + evidence 合成 explain 的机读文档（形状即 ADR 0042 决策四的 JSON 形态）。 **骨架是…** (1 connections) — `cli/gherkai_cli/render.py`
- **Any** (1 connections)
- **隧道凭据脱敏（ADR 0035 决策 5）：把文本里 `scheme://用户:口令@主机` 的 userinfo 段换成 `***`。…** (1 connections) — `core/gherkai_core/redact.py`
- **`https://u:p@host/x` → `https://***@host/x`；None 原样返回。** (1 connections) — `core/gherkai_core/redact.py`
- **递归脱敏 dict / list / tuple 里的全部字符串（键不动，只改值）；其它类型原样返回。** (1 connections) — `core/gherkai_core/redact.py`
- **parametrize** (1 connections)
- **隧道凭据脱敏的规则单测（ADR 0035 决策 5）。…** (1 connections) — `core/tests/test_redact.py`
- **规则直接作用在已序列化的整行上：结果仍能解析，字段值里的凭据被换掉。** (1 connections) — `core/tests/test_redact.py`
- **前一个字段的地址不带 @、后一个字段里有 @：匹配停在引号处，不跨字段吞掉内容。** (1 connections) — `core/tests/test_redact.py`
- **test_mask_is_three_stars_before_at()** (1 connections) — `core/tests/test_redact.py`

## Relationships

- [CLI Command Entrypoints](CLI_Command_Entrypoints.md) (4 shared connections)
- [Event Wire Serialization](Event_Wire_Serialization.md) (3 shared connections)
- [Explain Tree Rendering](Explain_Tree_Rendering.md) (2 shared connections)
- [Core Adapters Documentation](Core_Adapters_Documentation.md) (2 shared connections)
- [Result Store Serialization](Result_Store_Serialization.md) (1 shared connections)
- [Engine Listing and JSON Contract](Engine_Listing_and_JSON_Contract.md) (1 shared connections)
- [Run Definition Domain Model](Run_Definition_Domain_Model.md) (1 shared connections)
- [Result Tree Text Rendering](Result_Tree_Text_Rendering.md) (1 shared connections)
- [Agent Skill Reference Docs](Agent_Skill_Reference_Docs.md) (1 shared connections)

## Source Files

- `cli/gherkai_cli/render.py`
- `core/gherkai_core/redact.py`
- `core/tests/test_redact.py`

## Audit Trail

- EXTRACTED: 42 (95%)
- INFERRED: 2 (5%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*