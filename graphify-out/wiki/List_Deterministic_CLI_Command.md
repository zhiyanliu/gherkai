# List Deterministic CLI Command

> 4 nodes · cohesion 0.50

## Key Concepts

- **_resolve_steps_dir()** (6 connections) — `cli/gherkai_cli/__main__.py`
- **_cmd_list_deterministic()** (5 connections) — `cli/gherkai_cli/__main__.py`
- **解析使用方确定性 step 目录（ADR 0037 决策 4）：`--steps-dir` > env `GHERKAI_STEPS_DIR` > 默认…** (1 connections) — `cli/gherkai_cli/__main__.py`
- **按引擎列出确定性 step 清单（ADR 0036）：spawn worker 自述、CLI 只转述——core/CLI 不持有 pattern 语义（ADR…** (1 connections) — `cli/gherkai_cli/__main__.py`

## Relationships

- [CLI Run/Submit Commands](CLI_Run-Submit_Commands.md) (3 shared connections)
- [CLI Main Entry](CLI_Main_Entry.md) (2 shared connections)
- [CLI Run Entry Tests](CLI_Run_Entry_Tests.md) (1 shared connections)
- [Plan Command & Rendering](Plan_Command_%26_Rendering.md) (1 shared connections)

## Source Files

- `cli/gherkai_cli/__main__.py`

## Audit Trail

- EXTRACTED: 10 (100%)
- INFERRED: 0 (0%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*