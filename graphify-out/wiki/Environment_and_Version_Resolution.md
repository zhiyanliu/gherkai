# Environment and Version Resolution

> 7 nodes · cohesion 0.29

## Key Concepts

- **ValueError** (19 connections)
- **._resolve_version()** (4 connections) — `deploy_aws/gherkai_deploy_aws/stack.py`
- **_read_ssm_list()** (4 connections) — `runtime/gherkai_runtime/compose.py`
- **.from_env()** (3 connections) — `engines/novaact/gherkai_worker_novaact/lib/event_sink.py`
- **后端版本戳（PEP 440 字符串）：**`-c version=` 必给、无隐式默认**。 单一真源 = 发起这次部署的命令（`gherkai…** (1 connections) — `deploy_aws/gherkai_deploy_aws/stack.py`
- **从注入的 env 造（唯一读 env 处）。EVENTS_DDB_TABLE 非空 → DDB 态；否则 fd 态（EVENTS_FD 无/非法 → 回落…** (1 connections) — `engines/novaact/gherkai_worker_novaact/lib/event_sink.py`
- **读一个 SSM StringList 参数 → list[str]（subnet/sg 的 ID 列表，CDK 写、cli 读，ADR 0033）。 **空值…** (1 connections) — `runtime/gherkai_runtime/compose.py`

## Relationships

- [Backend Stack Constructs](Backend_Stack_Constructs.md) (3 shared connections)
- [Composition Root Wiring](Composition_Root_Wiring.md) (2 shared connections)
- [CDK Command Orchestration](CDK_Command_Orchestration.md) (2 shared connections)
- [Step Dispatch & Error Mapping](Step_Dispatch_%26_Error_Mapping.md) (2 shared connections)
- [Worker Event Sink](Worker_Event_Sink.md) (1 shared connections)
- [Fargate Network Resolution](Fargate_Network_Resolution.md) (1 shared connections)
- [Engine Ports & Adapters](Engine_Ports_%26_Adapters.md) (1 shared connections)
- [Cloud Backend CLI Tests](Cloud_Backend_CLI_Tests.md) (1 shared connections)
- [Run Schedule Orchestration](Run_Schedule_Orchestration.md) (1 shared connections)
- [Wire Protocol Serialization](Wire_Protocol_Serialization.md) (1 shared connections)
- [Deterministic Step Registry](Deterministic_Step_Registry.md) (1 shared connections)
- [Artifact S3 Upload](Artifact_S3_Upload.md) (1 shared connections)

## Source Files

- `deploy_aws/gherkai_deploy_aws/stack.py`
- `engines/novaact/gherkai_worker_novaact/lib/event_sink.py`
- `runtime/gherkai_runtime/compose.py`

## Audit Trail

- EXTRACTED: 9 (33%)
- INFERRED: 18 (67%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*