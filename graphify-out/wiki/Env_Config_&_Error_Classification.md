# Env Config & Error Classification

> 11 nodes · cohesion 0.18

## Key Concepts

- **ValueError** (19 connections)
- **_classify_act_error()** (9 connections) — `engines/novaact/gherkai_worker_novaact/run_scope.py`
- **_read_ssm_list()** (4 connections) — `runtime/gherkai_runtime/compose.py`
- **.from_env()** (3 connections) — `engines/novaact/gherkai_worker_novaact/lib/event_sink.py`
- **test_classify_unknown_falls_back_engine_error()** (3 connections) — `engines/novaact/tests/test_run_step.py`
- **test_classify_guardrail()** (2 connections) — `engines/novaact/tests/test_run_step.py`
- **test_classify_network_beats_sdk_type()** (2 connections) — `engines/novaact/tests/test_run_step.py`
- **test_classify_timeout()** (2 connections) — `engines/novaact/tests/test_run_step.py`
- **从注入的 env 造（唯一读 env 处）。EVENTS_DDB_TABLE 非空 → DDB 态；否则 fd 态（EVENTS_FD 无/非法 → 回落…** (1 connections) — `engines/novaact/gherkai_worker_novaact/lib/event_sink.py`
- **把 act/act_get 中途异常映射到规范化 errorType（ADR 0024/0028）。优先级： 网络瞬时 > Nova SDK…** (1 connections) — `engines/novaact/gherkai_worker_novaact/run_scope.py`
- **读一个 SSM StringList 参数 → list[str]（subnet/sg 的 ID 列表，CDK 写、cli 读，ADR 0033）。 **空值…** (1 connections) — `runtime/gherkai_runtime/compose.py`

## Relationships

- [Step Dispatch Execution](Step_Dispatch_Execution.md) (6 shared connections)
- [Transient Error Detection](Transient_Error_Detection.md) (3 shared connections)
- [Cloud Target Resolution](Cloud_Target_Resolution.md) (2 shared connections)
- [SSM Path & Client Composition](SSM_Path_%26_Client_Composition.md) (2 shared connections)
- [Provider Deploy Commands](Provider_Deploy_Commands.md) (2 shared connections)
- [Backend CDK Stack](Backend_CDK_Stack.md) (2 shared connections)
- [Worker Event Sink](Worker_Event_Sink.md) (1 shared connections)
- [Nova Act Worker](Nova_Act_Worker.md) (1 shared connections)
- [Engine Ports & Adapters](Engine_Ports_%26_Adapters.md) (1 shared connections)
- [Cloud Backend CLI Tests](Cloud_Backend_CLI_Tests.md) (1 shared connections)
- [Run Scheduling Engine](Run_Scheduling_Engine.md) (1 shared connections)
- [Event Progress Formatting](Event_Progress_Formatting.md) (1 shared connections)

## Source Files

- `engines/novaact/gherkai_worker_novaact/lib/event_sink.py`
- `engines/novaact/gherkai_worker_novaact/run_scope.py`
- `engines/novaact/tests/test_run_step.py`
- `runtime/gherkai_runtime/compose.py`

## Audit Trail

- EXTRACTED: 19 (51%)
- INFERRED: 18 (49%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*