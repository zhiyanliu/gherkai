# Skill Stage Materialization

> 21 nodes · cohesion 0.27

## Key Concepts

- **materialize.py** (15 connections) — `skills/gherkai-evals/materialize.py`
- **Path** (13 connections)
- **fail()** (11 connections) — `skills/gherkai-evals/materialize.py`
- **main()** (11 connections) — `skills/gherkai-evals/materialize.py`
- **prepare_cli()** (9 connections) — `skills/gherkai-evals/materialize.py`
- **assert_prepared()** (6 connections) — `skills/gherkai-evals/materialize.py`
- **assert_stage_isolated()** (5 connections) — `skills/gherkai-evals/materialize.py`
- **snapshot()** (5 connections) — `skills/gherkai-evals/materialize.py`
- **assert_no_installed_skill()** (4 connections) — `skills/gherkai-evals/materialize.py`
- **_cli_main_digest()** (4 connections) — `skills/gherkai-evals/materialize.py`
- **copy_fixture()** (4 connections) — `skills/gherkai-evals/materialize.py`
- **integrity_check()** (4 connections) — `skills/gherkai-evals/materialize.py`
- **_run()** (4 connections) — `skills/gherkai-evals/materialize.py`
- **_uv()** (4 connections) — `skills/gherkai-evals/materialize.py`
- **write_shim()** (4 connections) — `skills/gherkai-evals/materialize.py`
- **substitute_placeholders()** (3 connections) — `skills/gherkai-evals/materialize.py`
- **_now()** (2 connections) — `skills/gherkai-evals/materialize.py`
- **一次性把舞台要用的 CLI 与 midscene 装到仓库外（见模块头注释第 0 步）。** (1 connections) — `skills/gherkai-evals/materialize.py`
- **舞台只许指向已备好、且没被改过的仓库外 CLI；没备好或被改过就响亮失败，绝不回落到仓库 .venv。** (1 connections) — `skills/gherkai-evals/materialize.py`
- **舞台里不得有仓库根路径、不得有 SKILL.md（见模块头注释第 5 步）。** (1 connections) — `skills/gherkai-evals/materialize.py`
- **把一个真跑过的项目目录快照进 fixtures/<case>（物化的逆操作，见模块头注释）。** (1 connections) — `skills/gherkai-evals/materialize.py`

## Relationships

- No strong cross-community connections detected

## Source Files

- `skills/gherkai-evals/materialize.py`

## Audit Trail

- EXTRACTED: 56 (100%)
- INFERRED: 0 (0%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*