# Skill Install Command

> 20 nodes · cohesion 0.18

## Key Concepts

- **skill_install.py** (12 connections) — `cli/gherkai_cli/skill_install.py`
- **install()** (12 connections) — `cli/gherkai_cli/skill_install.py`
- **_ask_pointer()** (5 connections) — `cli/gherkai_cli/skill_install.py`
- **_print_skill()** (5 connections) — `cli/gherkai_cli/skill_install.py`
- **Path** (5 connections)
- **_stderr()** (5 connections) — `cli/gherkai_cli/skill_install.py`
- **_append_pointer()** (4 connections) — `cli/gherkai_cli/skill_install.py`
- **_converge()** (4 connections) — `cli/gherkai_cli/skill_install.py`
- **_is_ours()** (4 connections) — `cli/gherkai_cli/skill_install.py`
- **_packaged_skill_dir()** (4 connections) — `cli/gherkai_cli/skill_install.py`
- **_agents()** (2 connections) — `cli/gherkai_cli/skill_install.py`
- **`gherkai skill install`：把随 wheel 带的 agent skill 收敛安装到使用方项目 / 用户级 agent 目录（ADR…** (1 connections) — `cli/gherkai_cli/skill_install.py`
- **把提示那一行追加进 agent 指令文件（不存在就建）。已有即不动，返回 False。** (1 connections) — `cli/gherkai_cli/skill_install.py`
- **`skill install` 的全部行为。读 args 上的 `agent` / `dir` / `global_` / `print_only` /…** (1 connections) — `cli/gherkai_cli/skill_install.py`
- **诊断 → stderr（stdout 留给 `--print` 的管道产出）。** (1 connections) — `cli/gherkai_cli/skill_install.py`
- **包内那份 skill 的 Traversable（不落地成路径；要真路径的调用方自己套 `as_file`）。** (1 connections) — `cli/gherkai_cli/skill_install.py`
- **`--print`：把 SKILL.md 正文原样打到 stdout（不安装）。** (1 connections) — `cli/gherkai_cli/skill_install.py`
- **整目录收敛：删旧 → 整份拷 → 写标记。`__pycache__` / `*.pyc` 不拷（保「装完 = 包内那份 + 标记」）。** (1 connections) — `cli/gherkai_cli/skill_install.py`
- **删得起吗：不存在 / 空目录 / 带安装标记 → 是；其余（含目标是文件）→ 不是。** (1 connections) — `cli/gherkai_cli/skill_install.py`
- **交互终端下问一次（默认否）；非交互（管道 / CI）直接否，只打印那一行让人自己贴。** (1 connections) — `cli/gherkai_cli/skill_install.py`

## Relationships

- [CLI Command Entry Points](CLI_Command_Entry_Points.md) (1 shared connections)
- [CLI Main Flow Tests](CLI_Main_Flow_Tests.md) (1 shared connections)
- [CLI Parser Construction](CLI_Parser_Construction.md) (1 shared connections)

## Source Files

- `cli/gherkai_cli/skill_install.py`

## Audit Trail

- EXTRACTED: 37 (100%)
- INFERRED: 0 (0%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*