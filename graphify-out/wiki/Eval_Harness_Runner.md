# Eval Harness Runner

> 22 nodes · cohesion 0.18

## Key Concepts

- **run_evals.py** (11 connections) — `skills/gherkai-evals/run_evals.py`
- **run_one()** (8 connections) — `skills/gherkai-evals/run_evals.py`
- **Path** (6 connections)
- **trigger_eval.py** (5 connections) — `skills/gherkai-evals/trigger_eval.py`
- **resolve_installer()** (5 connections) — `skills/gherkai-evals/trigger_eval.py`
- **main()** (4 connections) — `skills/gherkai-evals/run_evals.py`
- **pollution_metrics()** (4 connections) — `skills/gherkai-evals/run_evals.py`
- **_purge_session_dir()** (4 connections) — `skills/gherkai-evals/run_evals.py`
- **fail()** (4 connections) — `skills/gherkai-evals/trigger_eval.py`
- **main()** (4 connections) — `skills/gherkai-evals/trigger_eval.py`
- **one()** (4 connections) — `skills/gherkai-evals/trigger_eval.py`
- **collect_outputs()** (3 connections) — `skills/gherkai-evals/run_evals.py`
- **fail()** (3 connections) — `skills/gherkai-evals/run_evals.py`
- **load_evals()** (3 connections) — `skills/gherkai-evals/run_evals.py`
- **materialize()** (3 connections) — `skills/gherkai-evals/run_evals.py`
- **Path** (3 connections)
- **parse_events()** (2 connections) — `skills/gherkai-evals/run_evals.py`
- **tool_calls_of()** (2 connections) — `skills/gherkai-evals/run_evals.py`
- **删掉 Claude Code 为这个舞台路径建的会话目录（含 memory/），保证每次运行从零开始。** (1 connections) — `skills/gherkai-evals/run_evals.py`
- **每轮必报的三个指标：污染（触仓库 / 触 skill 副本）与不可重放（联网）。事后 grep 才知道 = 太晚。 skill_dirs = 本次运行的临时…** (1 connections) — `skills/gherkai-evals/run_evals.py`
- **用哪个 gherkai 装 skill：优先仓库外那套；它被 `--prepare-cli` 剥掉了包内 skill 时回落到仓库 `.venv`。…** (1 connections) — `skills/gherkai-evals/trigger_eval.py`
- **跑一条查询，返回（是否触发, 前几次工具名）。** (1 connections) — `skills/gherkai-evals/trigger_eval.py`

## Relationships

- No strong cross-community connections detected

## Source Files

- `skills/gherkai-evals/run_evals.py`
- `skills/gherkai-evals/trigger_eval.py`

## Audit Trail

- EXTRACTED: 41 (100%)
- INFERRED: 0 (0%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*