# Release Notes Rendering

> 8 nodes · cohesion 0.43

## Key Concepts

- **ValueError** (18 connections)
- **main()** (5 connections) — `.github/scripts/release_notes.py`
- **section()** (5 connections) — `.github/scripts/release_notes.py`
- **release_notes.py** (4 connections) — `.github/scripts/release_notes.py`
- **render()** (3 connections) — `.github/scripts/release_notes.py`
- **skill_install_tag_problems()** (3 connections) — `.github/scripts/release_notes.py`
- **`## [version]` 到下一个 `## ` 之间的正文（不含标题行），两端空行去掉。找不到节 → ValueError。** (1 connections) — `.github/scripts/release_notes.py`
- **文档里 skill 安装命令钉的版本逐处对照 version；required 时一处都没有也算问题。返回带行号的问题描述，空列表即通过。** (1 connections) — `.github/scripts/release_notes.py`

## Relationships

- [Provider Deploy Commands](Provider_Deploy_Commands.md) (2 shared connections)
- [CDK Backend Stack](CDK_Backend_Stack.md) (2 shared connections)
- [Step and Scenario Execution](Step_and_Scenario_Execution.md) (2 shared connections)
- [Plan and Scope Seam](Plan_and_Scope_Seam.md) (1 shared connections)
- [Worker Log Event Formatting](Worker_Log_Event_Formatting.md) (1 shared connections)
- [Event Wire Serialization](Event_Wire_Serialization.md) (1 shared connections)
- [Deterministic Step Registry](Deterministic_Step_Registry.md) (1 shared connections)
- [Artifact Uploader (Python)](Artifact_Uploader_%28Python%29.md) (1 shared connections)
- [Worker Event Sink](Worker_Event_Sink.md) (1 shared connections)
- [Worker Job Source](Worker_Job_Source.md) (1 shared connections)
- [Transient Error Detection](Transient_Error_Detection.md) (1 shared connections)
- [SSM Path Naming](SSM_Path_Naming.md) (1 shared connections)

## Source Files

- `.github/scripts/release_notes.py`

## Audit Trail

- EXTRACTED: 11 (39%)
- INFERRED: 17 (61%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*