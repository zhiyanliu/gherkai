# Release Notes Tooling

> 16 nodes · cohesion 0.17

## Key Concepts

- **ValueError** (22 connections)
- **main()** (5 connections) — `.github/scripts/release_notes.py`
- **section()** (5 connections) — `.github/scripts/release_notes.py`
- **is_botocore_error()** (5 connections) — `runtime/gherkai_runtime/compose.py`
- **release_notes.py** (4 connections) — `.github/scripts/release_notes.py`
- **_read_ssm_list()** (4 connections) — `runtime/gherkai_runtime/compose.py`
- **.from_env()** (3 connections) — `engines/novaact/gherkai_worker_novaact/lib/event_sink.py`
- **render()** (3 connections) — `.github/scripts/release_notes.py`
- **skill_install_tag_problems()** (3 connections) — `.github/scripts/release_notes.py`
- **test_is_botocore_error_classifies()** (3 connections) — `runtime/tests/test_compose.py`
- **从注入的 env 造（唯一读 env 处）。EVENTS_DDB_TABLE 非空 → DDB 态；否则 fd 态（EVENTS_FD 无/非法 → 回落…** (1 connections) — `engines/novaact/gherkai_worker_novaact/lib/event_sink.py`
- **`## [version]` 到下一个 `## ` 之间的正文（不含标题行），两端空行去掉。找不到节 → ValueError。** (1 connections) — `.github/scripts/release_notes.py`
- **文档里 skill 安装命令钉的版本逐处对照 version；required 时一处都没有也算问题。返回带行号的问题描述，空列表即通过。** (1 connections) — `.github/scripts/release_notes.py`
- **BaseException** (1 connections)
- **是否 botocore 异常（云端不可达/权限/凭证/region 等）——入口前端据此把云端故障归到自己的退出码层。 惰性 import…** (1 connections) — `runtime/gherkai_runtime/compose.py`
- **读一个 SSM StringList 参数 → list[str]（subnet/sg 的 ID 列表，CDK 写、cli 读，ADR 0033）。 **空值…** (1 connections) — `runtime/gherkai_runtime/compose.py`

## Relationships

- [SSM Path Naming](SSM_Path_Naming.md) (4 shared connections)
- [Cloud Resource Resolution](Cloud_Resource_Resolution.md) (3 shared connections)
- [Backend CDK Stack](Backend_CDK_Stack.md) (2 shared connections)
- [Step Execution Dispatch](Step_Execution_Dispatch.md) (2 shared connections)
- [Event Sink and Redaction](Event_Sink_and_Redaction.md) (1 shared connections)
- [Scope Tag Grouping](Scope_Tag_Grouping.md) (1 shared connections)
- [Cloud Backend CLI Tests](Cloud_Backend_CLI_Tests.md) (1 shared connections)
- [Run Scheduling Core](Run_Scheduling_Core.md) (1 shared connections)
- [Typed Errors and Wire Protocol](Typed_Errors_and_Wire_Protocol.md) (1 shared connections)
- [Worker Deploy CLI](Worker_Deploy_CLI.md) (1 shared connections)
- [CDK Command Wrapper](CDK_Command_Wrapper.md) (1 shared connections)
- [Deterministic Step Registry](Deterministic_Step_Registry.md) (1 shared connections)

## Source Files

- `.github/scripts/release_notes.py`
- `engines/novaact/gherkai_worker_novaact/lib/event_sink.py`
- `runtime/gherkai_runtime/compose.py`
- `runtime/tests/test_compose.py`

## Audit Trail

- EXTRACTED: 22 (51%)
- INFERRED: 21 (49%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*