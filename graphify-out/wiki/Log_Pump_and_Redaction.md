# Log Pump and Redaction

> 23 nodes · cohesion 0.12

## Key Concepts

- **redact_url_userinfo()** (11 connections) — `core/gherkai_core/redact.py`
- **core/tests/test_redact.py** (11 connections) — `core/tests/test_redact.py`
- **gherkai_core/redact.py** (8 connections) — `core/gherkai_core/redact.py`
- **redact_deep()** (8 connections) — `core/gherkai_core/redact.py`
- **_pump_log()** (6 connections) — `core/gherkai_core/adapters/subprocess_engine.py`
- **test_json_field_boundary_is_not_crossed()** (3 connections) — `core/tests/test_redact.py`
- **test_redact_url_userinfo_cases()** (3 connections) — `core/tests/test_redact.py`
- **test_serialized_json_line_stays_valid_and_loses_credentials()** (3 connections) — `core/tests/test_redact.py`
- **test_pump_log_masks_tunnel_credentials_in_sink_and_stderr()** (3 connections) — `core/tests/test_subprocess_engine.py`
- **test_none_passes_through()** (2 connections) — `core/tests/test_redact.py`
- **test_redact_deep_recurses_values_and_leaves_keys_and_non_strings()** (2 connections) — `core/tests/test_redact.py`
- **test_redact_deep_scalars()** (2 connections) — `core/tests/test_redact.py`
- **把 worker 的 stdout（SDK 噪声，tag=out）/ stderr（诊断，tag=err）实时透传为本进程日志。 带 [worker…** (1 connections) — `core/gherkai_core/adapters/subprocess_engine.py`
- **Any** (1 connections)
- **隧道凭据脱敏（ADR 0035 决策 5）：把文本里 `scheme://用户:口令@主机` 的 userinfo 段换成 `***`。…** (1 connections) — `core/gherkai_core/redact.py`
- **`https://u:p@host/x` → `https://***@host/x`；None 原样返回。** (1 connections) — `core/gherkai_core/redact.py`
- **递归脱敏 dict / list / tuple 里的全部字符串（键不动，只改值）；其它类型原样返回。** (1 connections) — `core/gherkai_core/redact.py`
- **parametrize** (1 connections)
- **隧道凭据脱敏的规则单测（ADR 0035 决策 5）。…** (1 connections) — `core/tests/test_redact.py`
- **规则直接作用在已序列化的整行上：结果仍能解析，字段值里的凭据被换掉。** (1 connections) — `core/tests/test_redact.py`
- **前一个字段的地址不带 @、后一个字段里有 @：匹配停在引号处，不跨字段吞掉内容。** (1 connections) — `core/tests/test_redact.py`
- **test_mask_is_three_stars_before_at()** (1 connections) — `core/tests/test_redact.py`
- **worker 日志逐行转发时盖住隧道凭据（ADR 0035 决策 5）：写 log_sink 与写本进程 stderr 两条分支都要盖。 直接喂…** (1 connections) — `core/tests/test_subprocess_engine.py`

## Relationships

- [Job Domain Models](Job_Domain_Models.md) (3 shared connections)
- [Typed Errors and Wire Protocol](Typed_Errors_and_Wire_Protocol.md) (3 shared connections)
- [Subprocess Engine Adapter Tests](Subprocess_Engine_Adapter_Tests.md) (2 shared connections)
- [CLI Command Handlers](CLI_Command_Handlers.md) (2 shared connections)
- [Explain Rendering](Explain_Rendering.md) (2 shared connections)
- [Subprocess Worker Handle](Subprocess_Worker_Handle.md) (1 shared connections)

## Source Files

- `core/gherkai_core/adapters/subprocess_engine.py`
- `core/gherkai_core/redact.py`
- `core/tests/test_redact.py`
- `core/tests/test_subprocess_engine.py`

## Audit Trail

- EXTRACTED: 42 (98%)
- INFERRED: 1 (2%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*