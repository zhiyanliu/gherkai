# Terminal Color Policy

> 19 nodes · cohesion 0.20

## Key Concepts

- **use_color()** (11 connections) — `core/gherkai_core/termcolor.py`
- **test_termcolor.py** (11 connections) — `core/tests/test_termcolor.py`
- **termcolor.py** (8 connections) — `core/gherkai_core/termcolor.py`
- **_clean_env()** (6 connections) — `core/tests/test_termcolor.py`
- **test_stream_decides_when_no_env()** (5 connections) — `core/tests/test_termcolor.py`
- **_Tty** (5 connections) — `core/tests/test_termcolor.py`
- **color_env_override()** (4 connections) — `core/gherkai_core/termcolor.py`
- **_Pipe** (4 connections) — `core/tests/test_termcolor.py`
- **test_force_color_enables_on_pipe()** (4 connections) — `core/tests/test_termcolor.py`
- **test_no_color_non_empty_wins_over_tty()** (4 connections) — `core/tests/test_termcolor.py`
- **test_term_dumb_disables()** (4 connections) — `core/tests/test_termcolor.py`
- **test_broken_stream_counts_as_not_tty()** (3 connections) — `core/tests/test_termcolor.py`
- **stream_is_tty()** (2 connections) — `core/gherkai_core/termcolor.py`
- **终端颜色开关的统一策略：人读输出的颜色都经此判定（ADR 0047）。 规则：`NO_COLOR` 为非空值或 `TERM=dumb`…** (1 connections) — `core/gherkai_core/termcolor.py`
- **环境变量给出的强制结论：False（`NO_COLOR` 非空或 `TERM=dumb`）、True（`FORCE_COLOR`…** (1 connections) — `core/gherkai_core/termcolor.py`
- **写到 `stream` 的人读输出要不要带颜色：环境变量优先，否则看 `stream` 是否为终端。** (1 connections) — `core/gherkai_core/termcolor.py`
- **.isatty()** (1 connections) — `core/tests/test_termcolor.py`
- **终端颜色开关的统一策略（gherkai_core.termcolor，ADR 0047）：环境变量优先于目标流是否终端，非空语义同 no-color.org。** (1 connections) — `core/tests/test_termcolor.py`
- **.isatty()** (1 connections) — `core/tests/test_termcolor.py`

## Relationships

- [SQLite Event Log Adapter](SQLite_Event_Log_Adapter.md) (2 shared connections)
- [Human-Readable Text UI](Human-Readable_Text_UI.md) (2 shared connections)
- [Core Library Concepts & ADRs](Core_Library_Concepts_%26_ADRs.md) (1 shared connections)
- [Subprocess Engine Logging](Subprocess_Engine_Logging.md) (1 shared connections)
- [CLI JSON Contract Tests](CLI_JSON_Contract_Tests.md) (1 shared connections)

## Source Files

- `core/gherkai_core/termcolor.py`
- `core/tests/test_termcolor.py`

## Audit Trail

- EXTRACTED: 42 (100%)
- INFERRED: 0 (0%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*