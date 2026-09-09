# Worker Command Fixtures

> 4 nodes · cohesion 0.50

## Key Concepts

- **novaact_env_cmd()** (3 connections) — `runtime/tests/test_compose.py`
- **midscene_env_cmd()** (2 connections) — `runtime/tests/test_compose.py`
- **fixture** (2 connections)
- **定位链第一级钉死一个假 novaact cmd：自述用例只验「组合根怎么拼命令/收结果」，不依赖本机装了什么。** (1 connections) — `runtime/tests/test_compose.py`

## Relationships

- [Worker Command Resolution](Worker_Command_Resolution.md) (2 shared connections)

## Source Files

- `runtime/tests/test_compose.py`

## Audit Trail

- EXTRACTED: 5 (100%)
- INFERRED: 0 (0%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*