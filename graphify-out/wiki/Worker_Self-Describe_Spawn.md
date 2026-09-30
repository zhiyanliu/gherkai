# Worker Self-Describe Spawn

> 12 nodes · cohesion 0.20

## Key Concepts

- **_ask_worker()** (9 connections) — `runtime/gherkai_runtime/compose.py`
- **WorkerNotFoundError** (6 connections) — `runtime/gherkai_runtime/compose.py`
- **WorkerSelfDescribeError** (6 connections) — `runtime/gherkai_runtime/compose.py`
- **scrubbed_environ()** (5 connections) — `runtime/gherkai_runtime/compose.py`
- **RuntimeError** (4 connections)
- **.__init__()** (3 connections) — `runtime/gherkai_runtime/compose.py`
- **.__init__()** (2 connections) — `runtime/gherkai_runtime/compose.py`
- **.__init__()** (2 connections) — `runtime/gherkai_runtime/compose.py`
- **worker **起来了但自述失败**（非零退出）——与「定位不到」（WorkerNotFoundError）是两回事：最常见成因是使用方 `steps/`…** (1 connections) — `runtime/gherkai_runtime/compose.py`
- **定位链四级全 miss（ADR 0037 决策 3）：带引擎名 + 该引擎的安装指引，退出码交调用点。 **继承 RuntimeError…** (1 connections) — `runtime/gherkai_runtime/compose.py`
- **继承一份 os.environ、抹掉组合根拥有的那些键（见 `_COMPOSE_OWNED_WORKER_ENV`）——所有注入 env 的起手式。…** (1 connections) — `runtime/gherkai_runtime/compose.py`
- **spawn 一次某引擎 worker 的**非 job 入口**、收一行 JSON（ADR 0036「4.」/「5.」两个入口的共同机制）。 非 job…** (1 connections) — `runtime/gherkai_runtime/compose.py`

## Relationships

- [Cloud Composition Helpers](Cloud_Composition_Helpers.md) (5 shared connections)
- [Composition Root Helpers](Composition_Root_Helpers.md) (4 shared connections)
- [Engine Capability Queries](Engine_Capability_Queries.md) (3 shared connections)
- [Worker Log Event Formatting](Worker_Log_Event_Formatting.md) (2 shared connections)
- [Plan and Scope Seam](Plan_and_Scope_Seam.md) (1 shared connections)

## Source Files

- `runtime/gherkai_runtime/compose.py`

## Audit Trail

- EXTRACTED: 26 (93%)
- INFERRED: 2 (7%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*