# Presentation Environment Independence

> 5 nodes · cohesion 0.40

## Key Concepts

- **aws()** (4 connections) — `deploy_aws/tests/test_workers.py`
- **_presentation_is_environment_independent()** (3 connections) — `deploy_aws/tests/test_workers.py`
- **fixture** (3 connections)
- **_aws_env()** (2 connections) — `deploy_aws/tests/test_workers.py`
- **人读渲染（ADR 0047）不随运行测试的终端变化：固定关色、表格不按终端取宽——否则 `pytest -s` 在真实终端里会因 ANSI 与折行假红。** (1 connections) — `deploy_aws/tests/test_workers.py`

## Relationships

- [Worker Push Deploy Tests](Worker_Push_Deploy_Tests.md) (4 shared connections)
- [Worker Image Management](Worker_Image_Management.md) (1 shared connections)

## Source Files

- `deploy_aws/tests/test_workers.py`

## Audit Trail

- EXTRACTED: 9 (100%)
- INFERRED: 0 (0%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*