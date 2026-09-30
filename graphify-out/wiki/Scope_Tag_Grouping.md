# Scope Tag Grouping

> 14 nodes · cohesion 0.26

## Key Concepts

- **scope.py** (21 connections) — `core/gherkai_core/scope.py`
- **PlanError** (15 connections) — `core/gherkai_core/errors.py`
- **ParsedScenario** (14 connections) — `core/gherkai_core/parse.py`
- **_resolve_engine()** (6 connections) — `core/gherkai_core/scope.py`
- **_resolve_timeout()** (6 connections) — `core/gherkai_core/scope.py`
- **_scope_key()** (6 connections) — `core/gherkai_core/scope.py`
- **_values_with_prefix()** (6 connections) — `core/gherkai_core/scope.py`
- **feature 写法/配置违约，拒绝运行（ADR 0019/0025）：engine 冲突、多 @scope 值、步骤关键字判不出等。 定义在此（而非…** (1 connections) — `core/gherkai_core/errors.py`
- **parse → scope 之间的中间结果：纯净 Scenario + 它解析出的 tags。 tags 是 scope 分组（按…** (1 connections) — `core/gherkai_core/parse.py`
- **scope seam（ADR 0025）：解析后的 scenario 按 tag 分组 + engine/timeout 校验 → Job[]。 对外入口…** (1 connections) — `core/gherkai_core/scope.py`
- **从 tags 取某前缀的去重值（保序）。如 prefix='@scope:' → ['login']。where 是出错时的定位（scenario id，即…** (1 connections) — `core/gherkai_core/scope.py`
- **解析一个 scenario 的 scope 归属 → (scope_value 或 None, 用于派生的 scenario_id)。 多个不同 @scope…** (1 connections) — `core/gherkai_core/scope.py`
- **解析一个 scope 的 engine：缺省用 default；任一标了则继承；多个不同值报错（ADR 0019/0025）。** (1 connections) — `core/gherkai_core/scope.py`
- **解析一个 scope 的 job 墙钟预算：与 _resolve_engine 同构（ADR 0019 @timeout）。 缺省用 default；任一标了…** (1 connections) — `core/gherkai_core/scope.py`

## Relationships

- [Feature Planning Core](Feature_Planning_Core.md) (12 shared connections)
- [Gherkin Feature Parsing](Gherkin_Feature_Parsing.md) (6 shared connections)
- [Job Domain Models](Job_Domain_Models.md) (5 shared connections)
- [Plan Parsing Tests](Plan_Parsing_Tests.md) (2 shared connections)
- [Typed Errors and Wire Protocol](Typed_Errors_and_Wire_Protocol.md) (2 shared connections)
- [Release Notes Tooling](Release_Notes_Tooling.md) (1 shared connections)
- [CLI Command Handlers](CLI_Command_Handlers.md) (1 shared connections)
- [SSM Path Naming](SSM_Path_Naming.md) (1 shared connections)
- [Cloud Resource Resolution](Cloud_Resource_Resolution.md) (1 shared connections)
- [E2E Test Harness](E2E_Test_Harness.md) (1 shared connections)
- [Run Result Aggregation Tree](Run_Result_Aggregation_Tree.md) (1 shared connections)

## Source Files

- `core/gherkai_core/errors.py`
- `core/gherkai_core/parse.py`
- `core/gherkai_core/scope.py`

## Audit Trail

- EXTRACTED: 49 (86%)
- INFERRED: 8 (14%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*