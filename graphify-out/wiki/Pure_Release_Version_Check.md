# Pure Release Version Check

> 3 nodes · cohesion 0.67

## Key Concepts

- **is_pure_release()** (3 connections) — `runtime/gherkai_runtime/compose.py`
- **test_pure_release_predicate()** (2 connections) — `runtime/tests/test_compose.py`
- **版本是否「纯发行版」（PEP 440：无 .dev / .post / 本地段）——定位链第四级的门槛之一。 dev/post/本地段版本**不可能存在于…** (1 connections) — `runtime/gherkai_runtime/compose.py`

## Relationships

- [Composition Root Wiring](Composition_Root_Wiring.md) (1 shared connections)
- [Worker Command Resolution](Worker_Command_Resolution.md) (1 shared connections)

## Source Files

- `runtime/gherkai_runtime/compose.py`
- `runtime/tests/test_compose.py`

## Audit Trail

- EXTRACTED: 3 (75%)
- INFERRED: 1 (25%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*