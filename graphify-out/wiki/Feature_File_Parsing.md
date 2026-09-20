# Feature File Parsing

> 17 nodes · cohesion 0.15

## Key Concepts

- **parse.py** (16 connections) — `core/gherkai_core/parse.py`
- **parse_feature()** (15 connections) — `core/gherkai_core/parse.py`
- **_map_argument()** (5 connections) — `core/gherkai_core/parse.py`
- **_step_keyword()** (4 connections) — `core/gherkai_core/parse.py`
- **_index_ast_lines()** (3 connections) — `core/gherkai_core/parse.py`
- **_scenario_line_and_example_line()** (3 connections) — `core/gherkai_core/parse.py`
- **test_leading_and_keyword_fails_fast()** (3 connections) — `core/tests/test_plan.py`
- **test_star_step_keyword_fails_fast()** (3 connections) — `core/tests/test_plan.py`
- **StepArgument** (1 connections)
- **parse seam（ADR 0025）：.feature 文本 → 领域模型 Scenario/Step。 藏住第三方库 gherkin-…** (1 connections) — `core/gherkai_core/parse.py`
- **pickle step 的 argument（gherkin 内部形状）→ model.StepArgument（自有形状，不透传 pickle 子…** (1 connections) — `core/gherkai_core/parse.py`
- **pickle 顶层 astNodeIds → (scenario 行号, example 行号或 None)。 普通 scenario:…** (1 connections) — `core/gherkai_core/parse.py`
- **解析一个 .feature 文本 → 展开后的 ParsedScenario 列表（id/行号已派生、带 tags）。 uri 既是 id 前缀，也是…** (1 connections) — `core/gherkai_core/parse.py`
- **pickle step type → 派发关键字（Given/When/Then）。type='Unknown' 一律 fail-fast。 Compiler…** (1 connections) — `core/gherkai_core/parse.py`
- **建 AST 节点 id → location.line 的索引，供 pickle 的 astNodeIds 回查行号。 只记 **scenario…** (1 connections) — `core/gherkai_core/parse.py`
- **`*` 步骤 type='Unknown'（gherkin 实测）→ PlanError,不静默兜底成 Given（假绿方向的错标）。** (1 connections) — `core/tests/test_plan.py`
- **无前驱非连接词的首条 And 同判不出 → PlanError;有前驱的 And 正常继承不受影响。** (1 connections) — `core/tests/test_plan.py`

## Relationships

- [Scope Tag Resolution](Scope_Tag_Resolution.md) (6 shared connections)
- [Run Metadata & S3 Offload](Run_Metadata_%26_S3_Offload.md) (6 shared connections)
- [Plan Parsing Tests](Plan_Parsing_Tests.md) (3 shared connections)
- [CLI Command Dispatch](CLI_Command_Dispatch.md) (2 shared connections)
- [Plan Job Generation](Plan_Job_Generation.md) (2 shared connections)
- [Core Typed Errors](Core_Typed_Errors.md) (1 shared connections)
- [Run State Rendering](Run_State_Rendering.md) (1 shared connections)

## Source Files

- `core/gherkai_core/parse.py`
- `core/tests/test_plan.py`

## Audit Trail

- EXTRACTED: 40 (98%)
- INFERRED: 1 (2%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*