# Local Stores & Deterministic Query

> 20 nodes · cohesion 0.11

## Key Concepts

- **query_deterministic()** (9 connections) — `runtime/gherkai_runtime/compose.py`
- **Path** (7 connections)
- **build_local_stores()** (6 connections) — `runtime/gherkai_runtime/compose.py`
- **match_deterministic()** (6 connections) — `runtime/gherkai_runtime/compose.py`
- **prune_empty_dirs()** (6 connections) — `runtime/gherkai_runtime/compose.py`
- **test_self_describe_miss_raises_worker_not_found()** (4 connections) — `runtime/tests/test_compose.py`
- **test_query_deterministic_injects_steps_dir_env()** (3 connections) — `runtime/tests/test_compose.py`
- **test_match_deterministic_feeds_stdin_and_parses()** (2 connections) — `runtime/tests/test_compose.py`
- **test_prune_empty_dirs_keeps_nonempty()** (2 connections) — `runtime/tests/test_compose.py`
- **test_prune_empty_dirs_noop_when_missing()** (2 connections) — `runtime/tests/test_compose.py`
- **test_prune_empty_dirs_removes_empty_tree()** (2 connections) — `runtime/tests/test_compose.py`
- **test_query_deterministic_parses_worker_json()** (2 connections) — `runtime/tests/test_compose.py`
- **test_query_deterministic_unknown_engine()** (2 connections) — `runtime/tests/test_compose.py`
- **test_query_deterministic_worker_failure_raises()** (2 connections) — `runtime/tests/test_compose.py`
- **自底向上删 root 下的空目录（含 root 自身若最终空）——只删空的（ADR 0029 cloud 清理本地空壳）。…** (1 connections) — `runtime/gherkai_runtime/compose.py`
- **查询某引擎 worker 的确定性能力清单（ADR 0036）：spawn `worker --list-deterministic` 收 JSON。…** (1 connections) — `runtime/gherkai_runtime/compose.py`
- **批量问某引擎 worker「这些 step 文本各命中哪条确定性模式」（ADR 0036 决策 4，plan 标注用）。 spawn `worker…** (1 connections) — `runtime/gherkai_runtime/compose.py`
- **本地文件三层 store + local artifacts descriptor（file:// 完整路径）。 落…** (1 connections) — `runtime/gherkai_runtime/compose.py`
- **自述入口同样加载 steps 目录（ADR 0037 决策 4）→ steps_dir 经 env 注入，故 list-deterministic 的清单…** (1 connections) — `runtime/tests/test_compose.py`
- **定位链 miss 时自述入口抛 WorkerNotFoundError（而非「起不来」的通用 RuntimeError）—— 调用点据此分叉：list-…** (1 connections) — `runtime/tests/test_compose.py`

## Relationships

- [Worker Command Resolution](Worker_Command_Resolution.md) (9 shared connections)
- [Composition Root Wiring](Composition_Root_Wiring.md) (4 shared connections)
- [S3 ReportStore & Subprocess Engine](S3_ReportStore_%26_Subprocess_Engine.md) (3 shared connections)
- [Engine Resolver Building](Engine_Resolver_Building.md) (2 shared connections)
- [DynamoDB RunStore Conditional Writes](DynamoDB_RunStore_Conditional_Writes.md) (1 shared connections)
- [Run Persistence Orchestration](Run_Persistence_Orchestration.md) (1 shared connections)
- [Render & ReportStore Local](Render_%26_ReportStore_Local.md) (1 shared connections)

## Source Files

- `runtime/gherkai_runtime/compose.py`
- `runtime/tests/test_compose.py`

## Audit Trail

- EXTRACTED: 38 (93%)
- INFERRED: 3 (7%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*