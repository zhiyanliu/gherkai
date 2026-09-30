# Feature File Parsing

> 13 nodes · cohesion 0.21

## Key Concepts

- **parse.py** (17 connections) — `core/gherkai_core/parse.py`
- **parse_feature()** (15 connections) — `core/gherkai_core/parse.py`
- **_map_argument()** (5 connections) — `core/gherkai_core/parse.py`
- **_step_keyword()** (4 connections) — `core/gherkai_core/parse.py`
- **_index_ast_lines()** (3 connections) — `core/gherkai_core/parse.py`
- **_scenario_line_and_example_line()** (3 connections) — `core/gherkai_core/parse.py`
- **StepArgument** (1 connections)
- **parse seam（ADR 0025）：.feature 文本 → 领域模型 Scenario/Step。 藏住第三方库 gherkin-…** (1 connections) — `core/gherkai_core/parse.py`
- **pickle step 的 argument（gherkin 内部形状）→ model.StepArgument（自有形状，不透传 pickle 子…** (1 connections) — `core/gherkai_core/parse.py`
- **pickle 顶层 astNodeIds → (scenario 行号, example 行号或 None)。 普通 scenario:…** (1 connections) — `core/gherkai_core/parse.py`
- **解析一个 .feature 文本 → 展开后的 ParsedScenario 列表（id/行号已派生、带 tags）。 uri 既是 id 前缀，也是…** (1 connections) — `core/gherkai_core/parse.py`
- **pickle step type → 派发关键字（Given/When/Then）。type='Unknown' 一律 fail-fast。 Compiler…** (1 connections) — `core/gherkai_core/parse.py`
- **建 AST 节点 id → location.line 的索引，供 pickle 的 astNodeIds 回查行号。 只记 **scenario…** (1 connections) — `core/gherkai_core/parse.py`

## Relationships

- [Plan and Scope Seam](Plan_and_Scope_Seam.md) (10 shared connections)
- [Run Definition Domain Model](Run_Definition_Domain_Model.md) (6 shared connections)
- [Core Adapters Documentation](Core_Adapters_Documentation.md) (3 shared connections)
- [CLI Command Entrypoints](CLI_Command_Entrypoints.md) (2 shared connections)
- [Package Contributor Docs](Package_Contributor_Docs.md) (1 shared connections)

## Source Files

- `core/gherkai_core/parse.py`

## Audit Trail

- EXTRACTED: 36 (95%)
- INFERRED: 2 (5%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*