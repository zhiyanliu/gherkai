# Fargate Network Resolution

> 6 nodes · cohesion 0.33

## Key Concepts

- **resolve_network()** (9 connections) — `runtime/gherkai_runtime/compose.py`
- **test_resolve_network_empty_ssm_fails_fast()** (2 connections) — `runtime/tests/test_compose.py`
- **test_resolve_network_explicit_overrides_skip_ssm()** (2 connections) — `runtime/tests/test_compose.py`
- **test_resolve_network_partial_override_reads_only_missing()** (2 connections) — `runtime/tests/test_compose.py`
- **test_resolve_network_reads_ssm_when_missing()** (2 connections) — `runtime/tests/test_compose.py`
- **Fargate awsvpcConfiguration（ADR 0033）：subnet/sg 未显式给 → 读含 prefix 的 SSM 路径（CDK…** (1 connections) — `runtime/gherkai_runtime/compose.py`

## Relationships

- [Worker Command Resolution](Worker_Command_Resolution.md) (4 shared connections)
- [Composition Root Wiring](Composition_Root_Wiring.md) (3 shared connections)
- [Environment and Version Resolution](Environment_and_Version_Resolution.md) (1 shared connections)

## Source Files

- `runtime/gherkai_runtime/compose.py`
- `runtime/tests/test_compose.py`

## Audit Trail

- EXTRACTED: 13 (100%)
- INFERRED: 0 (0%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*