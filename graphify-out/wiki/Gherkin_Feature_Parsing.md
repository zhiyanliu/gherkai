# Gherkin Feature Parsing

> 17 nodes · cohesion 0.15

## Key Concepts

- **parse.py** (15 connections) — `core/gherkai_core/parse.py`
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

- [Scope Parsing & Plan Errors](Scope_Parsing_%26_Plan_Errors.md) (6 shared connections)
- [Job Explain & S3 Offload](Job_Explain_%26_S3_Offload.md) (6 shared connections)
- [Feature Plan Tests](Feature_Plan_Tests.md) (3 shared connections)
- [CLI Command Entry Points](CLI_Command_Entry_Points.md) (2 shared connections)
- [Typed Errors & Severity](Typed_Errors_%26_Severity.md) (1 shared connections)
- [Cloud Boto3 Guards & EventLog](Cloud_Boto3_Guards_%26_EventLog.md) (1 shared connections)
- [Feature Plan to Jobs](Feature_Plan_to_Jobs.md) (1 shared connections)

## Source Files

- `core/gherkai_core/parse.py`
- `core/tests/test_plan.py`

## Audit Trail

- EXTRACTED: 40 (100%)
- INFERRED: 0 (0%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*