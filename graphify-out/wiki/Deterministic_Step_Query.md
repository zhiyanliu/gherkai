# Deterministic Step Query

> 15 nodes · cohesion 0.14

## Key Concepts

- **query_deterministic()** (9 connections) — `runtime/gherkai_runtime/compose.py`
- **Path** (8 connections)
- **match_deterministic()** (6 connections) — `runtime/gherkai_runtime/compose.py`
- **test_self_describe_miss_raises_worker_not_found()** (4 connections) — `runtime/tests/test_compose.py`
- **local_artifact_locations()** (3 connections) — `runtime/gherkai_runtime/compose.py`
- **test_query_deterministic_injects_steps_dir_env()** (3 connections) — `runtime/tests/test_compose.py`
- **test_match_deterministic_feeds_stdin_and_parses()** (2 connections) — `runtime/tests/test_compose.py`
- **test_query_deterministic_parses_worker_json()** (2 connections) — `runtime/tests/test_compose.py`
- **test_query_deterministic_unknown_engine()** (2 connections) — `runtime/tests/test_compose.py`
- **test_query_deterministic_worker_failure_raises()** (2 connections) — `runtime/tests/test_compose.py`
- **查询某引擎 worker 的确定性能力清单（ADR 0036）：spawn `worker --list-deterministic` 收 JSON。…** (1 connections) — `runtime/gherkai_runtime/compose.py`
- **批量问某引擎 worker「这些 step 文本各命中哪条确定性模式」（ADR 0036 决策 4，plan 标注用）。 spawn `worker…** (1 connections) — `runtime/gherkai_runtime/compose.py`
- **local 档一个 run 的产物落点（全 file:// URI）：run_meta / run_state / jobs_dir /…** (1 connections) — `runtime/gherkai_runtime/compose.py`
- **自述入口同样加载 steps 目录（ADR 0037 决策 4）→ steps_dir 经 env 注入，故 list-deterministic 的清单…** (1 connections) — `runtime/tests/test_compose.py`
- **定位链 miss 时自述入口抛 WorkerNotFoundError（而非「起不来」的通用 RuntimeError）—— 调用点据此分叉：list-…** (1 connections) — `runtime/tests/test_compose.py`

## Relationships

- [Cloud Target & Worker Resolution](Cloud_Target_%26_Worker_Resolution.md) (7 shared connections)
- [Runtime Composition Root](Runtime_Composition_Root.md) (3 shared connections)
- [S3 Report Store & Control Plane](S3_Report_Store_%26_Control_Plane.md) (3 shared connections)
- [Engine Composition Helpers](Engine_Composition_Helpers.md) (2 shared connections)
- [Local Result Store & Persistence](Local_Result_Store_%26_Persistence.md) (1 shared connections)

## Source Files

- `runtime/gherkai_runtime/compose.py`
- `runtime/tests/test_compose.py`

## Audit Trail

- EXTRACTED: 31 (100%)
- INFERRED: 0 (0%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*