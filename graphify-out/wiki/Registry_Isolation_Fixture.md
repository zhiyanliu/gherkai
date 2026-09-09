# Registry Isolation Fixture

> 3 nodes · cohesion 0.67

## Key Concepts

- **_isolate()** (3 connections) — `engines/novaact/tests/test_user_steps.py`
- **fixture** (1 connections)
- **注册表 snapshot/restore + 清掉本测试塞进 sys.modules 的合成模块（跨文件顺序性假绿/假红的防线）。** (1 connections) — `engines/novaact/tests/test_user_steps.py`

## Relationships

- [User Steps Directory Loading](User_Steps_Directory_Loading.md) (1 shared connections)

## Source Files

- `engines/novaact/tests/test_user_steps.py`

## Audit Trail

- EXTRACTED: 3 (100%)
- INFERRED: 0 (0%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*