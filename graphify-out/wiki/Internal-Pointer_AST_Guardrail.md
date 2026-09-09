# Internal-Pointer AST Guardrail

> 11 nodes · cohesion 0.27

## Key Concepts

- **test_user_facing_messages.py** (9 connections) — `cli/tests/test_user_facing_messages.py`
- **_docstring_node_ids()** (4 connections) — `cli/tests/test_user_facing_messages.py`
- **test_no_internal_pointers_in_user_facing_text()** (4 connections) — `cli/tests/test_user_facing_messages.py`
- **_scan_midscene()** (3 connections) — `cli/tests/test_user_facing_messages.py`
- **_scan_python()** (3 connections) — `cli/tests/test_user_facing_messages.py`
- **_strip_ts_comments()** (3 connections) — `cli/tests/test_user_facing_messages.py`
- **AST** (2 connections)
- **护栏：产品面文案不带内部指代（CLAUDE.md「代码纪律」同名条的机器执行体）。…** (1 connections) — `cli/tests/test_user_facing_messages.py`
- **module / class / def 的 docstring 常量节点 id——放行面（指针的合法归宿）。** (1 connections) — `cli/tests/test_user_facing_messages.py`
- **去掉 `/* */`（保行号：注释体换成等量换行）与行尾 `//` 之后的内容 → [(行号, 剩余代码)]。 切 `//`…** (1 connections) — `cli/tests/test_user_facing_messages.py`
- **五个生产包的非 docstring 字面量 + Midscene 源的非注释行：一处内部指代都不许有。** (1 connections) — `cli/tests/test_user_facing_messages.py`

## Relationships

- [Project Conventions & README Guards](Project_Conventions_%26_README_Guards.md) (1 shared connections)
- [ADR Index & Dev Docs](ADR_Index_%26_Dev_Docs.md) (1 shared connections)

## Source Files

- `cli/tests/test_user_facing_messages.py`

## Audit Trail

- EXTRACTED: 17 (100%)
- INFERRED: 0 (0%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*