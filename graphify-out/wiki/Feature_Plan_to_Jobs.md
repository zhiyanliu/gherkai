# Feature Plan to Jobs

> 17 nodes · cohesion 0.19

## Key Concepts

- **FeatureSource** (30 connections) — `core/gherkai_core/scope.py`
- **plan()** (24 connections) — `core/gherkai_core/scope.py`
- **PlanConfig** (13 connections) — `core/gherkai_core/scope.py`
- **test_scope_id_collision_across_files_errors()** (5 connections) — `core/tests/test_plan.py`
- **test_assertion_votes_from_config_propagates_to_all_jobs()** (4 connections) — `core/tests/test_plan.py`
- **test_plan_select_dropped_scope_does_not_block_iteration()** (4 connections) — `core/tests/test_plan.py`
- **test_plan_select_keeps_scope_engine_and_timeout()** (4 connections) — `core/tests/test_plan.py`
- **test_scope_id_collision_errors_even_when_narrowed_away()** (4 connections) — `core/tests/test_plan.py`
- **test_cross_file_scope_merge_warns()** (3 connections) — `core/tests/test_plan.py`
- **test_distinct_uri_ok()** (3 connections) — `core/tests/test_plan.py`
- **test_duplicate_uri_errors()** (3 connections) — `core/tests/test_plan.py`
- **Job** (1 connections)
- **core 窄腰第一步：一组 .feature → 可调度的 Job 列表（ADR 0025）。 select（ADR 0041 决策一）：scenario…** (1 connections) — `core/gherkai_core/scope.py`
- **plan 的输入：feature 文件内容（非路径——core 不碰 FS，ADR 0025）。** (1 connections) — `core/gherkai_core/scope.py`
- **跨文件同构输入：两种 features 顺序都报错（此前只有「未标在前」那种顺序才打得出 warning）。** (1 connections) — `core/tests/test_plan.py`
- **撞名检测在施加 select 之前：收窄到只跑 named 那个 scope 也照样退——撞的是 scope_id 命名空间，不是本次跑哪几条。…** (1 connections) — `core/tests/test_plan.py`
- **整组被筛掉的 scope 里的 tag 冲突不拦本次迭代（空组在解析 engine/timeout 之前跳过）； 但「一个 scenario 多个…** (1 connections) — `core/tests/test_plan.py`

## Relationships

- [Feature Plan Tests](Feature_Plan_Tests.md) (17 shared connections)
- [Scope Parsing & Plan Errors](Scope_Parsing_%26_Plan_Errors.md) (12 shared connections)
- [S3 Report Store & Control Plane](S3_Report_Store_%26_Control_Plane.md) (6 shared connections)
- [Cloud Resource Preflight](Cloud_Resource_Preflight.md) (4 shared connections)
- [End-to-End Test Harness](End-to-End_Test_Harness.md) (3 shared connections)
- [Job Explain & S3 Offload](Job_Explain_%26_S3_Offload.md) (3 shared connections)
- [CLI Command Entry Points](CLI_Command_Entry_Points.md) (2 shared connections)
- [Engine Composition Helpers](Engine_Composition_Helpers.md) (1 shared connections)
- [Runtime Composition Root](Runtime_Composition_Root.md) (1 shared connections)
- [Backend Version Skew Check](Backend_Version_Skew_Check.md) (1 shared connections)
- [Gherkin Feature Parsing](Gherkin_Feature_Parsing.md) (1 shared connections)

## Source Files

- `core/gherkai_core/scope.py`
- `core/tests/test_plan.py`

## Audit Trail

- EXTRACTED: 59 (77%)
- INFERRED: 18 (23%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*