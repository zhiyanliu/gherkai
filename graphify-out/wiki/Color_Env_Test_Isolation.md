# Color Env Test Isolation

> 3 nodes · cohesion 0.67

## Key Concepts

- **_color_env_independent()** (4 connections) — `core/tests/test_subprocess_engine.py`
- **_reset_scope_colors()** (2 connections) — `core/gherkai_core/adapters/subprocess_engine.py`
- **本模块的颜色断言不受运行测试的 shell 影响：清掉 NO_COLOR / FORCE_COLOR / TERM=dumb，让「是否终端」成为唯一变量。** (1 connections) — `core/tests/test_subprocess_engine.py`

## Relationships

- [Subprocess Engine Adapter](Subprocess_Engine_Adapter.md) (1 shared connections)
- [Test Fixtures And Env](Test_Fixtures_And_Env.md) (1 shared connections)
- [Subprocess Engine Tests](Subprocess_Engine_Tests.md) (1 shared connections)

## Source Files

- `core/gherkai_core/adapters/subprocess_engine.py`
- `core/tests/test_subprocess_engine.py`

## Audit Trail

- EXTRACTED: 5 (100%)
- INFERRED: 0 (0%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*