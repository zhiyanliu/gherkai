# CLI Test Fixtures

> 5 nodes · cohesion 0.40

## Key Concepts

- **cli/tests/conftest.py** (4 connections) — `cli/tests/conftest.py`
- **_presentation_is_environment_independent()** (3 connections) — `cli/tests/conftest.py`
- **_stub_engine_capabilities()** (2 connections) — `cli/tests/conftest.py`
- **cli 测试的公共夹具。 **默认不 spawn 真 worker 问能力自述**：`run`/`submit` 的运行前检查、`list-…** (1 connections) — `cli/tests/conftest.py`
- **人读渲染（ADR 0047）不随运行测试的终端变化：固定关色、表格不按终端取宽——否则 `pytest -s` 在真实终端里会因 ANSI 与折行假红。** (1 connections) — `cli/tests/conftest.py`

## Relationships

- [Test Fixtures And Env](Test_Fixtures_And_Env.md) (2 shared connections)
- [SSM Paths And Compose](SSM_Paths_And_Compose.md) (1 shared connections)

## Source Files

- `cli/tests/conftest.py`

## Audit Trail

- EXTRACTED: 7 (100%)
- INFERRED: 0 (0%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*