# Scenario Key Derivation

> 8 nodes · cohesion 0.25

## Key Concepts

- **scenario_key()** (7 connections) — `engines/novaact/gherkai_worker_novaact/evidence.py`
- **test_scenario_key_does_not_use_display_name()** (3 connections) — `engines/novaact/tests/test_evidence.py`
- **test_scenario_key_no_collision_after_escaping()** (3 connections) — `engines/novaact/tests/test_evidence.py`
- **test_scenario_key_is_deterministic_and_escapes_separators()** (2 connections) — `engines/novaact/tests/test_evidence.py`
- **test_scenario_key_survives_non_ascii_and_empty_ids()** (2 connections) — `engines/novaact/tests/test_evidence.py`
- **`<uri>:<行>[:<example 行>]` → 目录名段：转义分隔符 + 尾附 id 短哈希（ADR 0042 决策一）。…** (1 connections) — `engines/novaact/gherkai_worker_novaact/evidence.py`
- **转义会把这两个 id 压成同一串（uri 里的分隔符差异），短哈希把它们分开——撞了就会让 evidence 静默互相覆盖。** (1 connections) — `engines/novaact/tests/test_evidence.py`
- **同一份显示名可属不同 scenario（同文件重名 / @scope 跨文件合并）→ 键只由 id 派生。** (1 connections) — `engines/novaact/tests/test_evidence.py`

## Relationships

- [Evidence Artifact Upload](Evidence_Artifact_Upload.md) (4 shared connections)
- [AWS Test Fixtures (moto)](AWS_Test_Fixtures_%28moto%29.md) (2 shared connections)

## Source Files

- `engines/novaact/gherkai_worker_novaact/evidence.py`
- `engines/novaact/tests/test_evidence.py`

## Audit Trail

- EXTRACTED: 13 (100%)
- INFERRED: 0 (0%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*