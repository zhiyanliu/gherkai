# Single-Line Error Text

> 6 nodes · cohesion 0.33

## Key Concepts

- **_error_text()** (8 connections) — `engines/novaact/gherkai_worker_novaact/run_scope.py`
- **test_error_text_prefers_sdk_message_and_is_single_line()** (3 connections) — `engines/novaact/tests/test_evidence.py`
- **test_error_text_redacts_before_truncation()** (3 connections) — `engines/novaact/tests/test_evidence.py`
- **异常 → 一行「类型: 信息」，作 step_done 的 message 与 evidence 的 act.error（ADR 0042 决策三/决策一）。…** (1 connections) — `engines/novaact/gherkai_worker_novaact/run_scope.py`
- **SDK 异常的 str() 是多行 repr（实际运行暴露：ActTimeoutError 把「原因」撑成十几行）——取 .message…** (1 connections) — `engines/novaact/tests/test_evidence.py`
- **隧道地址落在 300 字边界上时先脱敏再截断（ADR 0035 决策 5）：截在 userinfo 中间会丢掉 `@`、出口处的规则就抓不到。** (1 connections) — `engines/novaact/tests/test_evidence.py`

## Relationships

- [Scenario Evidence Keys](Scenario_Evidence_Keys.md) (3 shared connections)
- [Worker Event Sink](Worker_Event_Sink.md) (1 shared connections)
- [Step and Scenario Execution](Step_and_Scenario_Execution.md) (1 shared connections)
- [Transient Error Detection](Transient_Error_Detection.md) (1 shared connections)
- [Nova Act Worker Runtime](Nova_Act_Worker_Runtime.md) (1 shared connections)

## Source Files

- `engines/novaact/gherkai_worker_novaact/run_scope.py`
- `engines/novaact/tests/test_evidence.py`

## Audit Trail

- EXTRACTED: 12 (100%)
- INFERRED: 0 (0%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*